from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import Producto,Venta,DetalleVenta
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.forms import modelform_factory
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from django.utils import timezone

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Usuario o contraseña incorrectos", extra_tags="auth")

    return render(request, "productos/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.", extra_tags="auth")
    return redirect("login")


@login_required
@never_cache
def home_view(request):
    productos = Producto.objects.all()
    return render(request, "productos/home.html", {"productos": productos})

@login_required
@never_cache
def agregar_producto(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        codigo = request.POST.get("codigo")
        precio_venta = request.POST.get("precio_venta")
        costo = request.POST.get("costo")
        stock = request.POST.get("stock")
        foto = request.FILES.get("foto")  

        Producto.objects.create(
            nombre=nombre,
            codigo=codigo,
            precio_venta=precio_venta,
            costo=costo,
            stock=stock,
            foto=foto
        )
        return redirect("productos_list")

    return render(request, "productos/agregar_producto.html")


@login_required
@never_cache
def modificar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == "POST":
        producto.nombre = request.POST.get("nombre")
        producto.codigo = request.POST.get("codigo")
        producto.precio_venta = request.POST.get("precio_venta")
        producto.costo = request.POST.get("costo")
        producto.stock = request.POST.get("stock")

        if request.FILES.get("foto"):
            producto.foto = request.FILES.get("foto")

        producto.save()
        return redirect("productos_list")

    return render(request, "productos/modificar_producto.html", {"producto": producto})


@login_required
@never_cache
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == "POST":
        producto.delete()
        return redirect("productos_list")
    return redirect("productos_list")


@login_required
def registrar_venta(request):
    productos = Producto.objects.filter(stock__gt=0)

    if request.method == 'POST':
        total = 0
        venta = Venta.objects.create(usuario=request.user, total=0)
        items_validos = 0  

        for key in request.POST:
            if key.startswith('producto_'):
                idx = key.split('_')[1]
                producto_id = request.POST.get(f'producto_{idx}')
                cantidad_raw = request.POST.get(f'cantidad_{idx}', '').strip()

                if not producto_id or not cantidad_raw:
                    continue
                try:
                    cantidad = int(cantidad_raw)
                except ValueError:
                    cantidad = 0
                if cantidad <= 0:
                    continue

                try:
                    producto = Producto.objects.get(id=producto_id)
                except Producto.DoesNotExist:
                    continue

                if producto.stock < cantidad:
                    messages.error(
                        request,
                        f"No hay suficiente stock de {producto.nombre}. Stock disponible: {producto.stock}"
                    )
                    venta.delete()
                    return redirect('registrar_venta')

                precio = producto.precio_venta
                subtotal = cantidad * precio
                total += subtotal

                producto.stock -= cantidad
                producto.save()

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal
                )

                items_validos += 1

        if items_validos == 0:
            venta.delete()
            messages.error(request, "Debes seleccionar al menos un producto y una cantidad válida (mayor a 0).")
            return redirect('registrar_venta')

        venta.total = total
        venta.save()
        messages.success(request, "Venta registrada correctamente.")
        return redirect('listar_ventas')

    return render(request, 'productos/registrar_venta.html', {'productos': productos})




@login_required
@never_cache
def listar_ventas(request):
    ventas = Venta.objects.select_related('usuario').prefetch_related('detalles__producto').order_by('-fecha')
    return render(request, 'productos/listar_ventas.html', {'ventas': ventas})


@login_required
def modificar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    productos = Producto.objects.all()

    if request.method == 'POST':
        for detalle in venta.detalles.all():
            detalle.producto.stock += detalle.cantidad
            detalle.producto.save()
        venta.detalles.all().delete()

        total = 0

        for key in request.POST:
            if key.startswith('producto_'):
                idx = key.split('_')[1]
                producto_id = request.POST.get(f'producto_{idx}')
                cantidad = int(request.POST.get(f'cantidad_{idx}', 0))

                if not producto_id or cantidad <= 0:
                    continue

                producto = Producto.objects.get(id=producto_id)

                if producto.stock < cantidad:
                    messages.error(request, f"No hay suficiente stock de {producto.nombre}. Stock disponible: {producto.stock}")
                    return redirect('modificar_venta', id=venta.id)

                precio = producto.precio_venta
                subtotal = cantidad * precio
                total += subtotal

                producto.stock -= cantidad
                producto.save()

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal
                )

        venta.total = total
        venta.save()
        messages.success(request, f"Venta #{venta.id} actualizada correctamente.")
        return redirect('listar_ventas')

    detalles = venta.detalles.all()
    return render(request, 'productos/modificar_venta.html', {
        'venta': venta,
        'productos': productos,
        'detalles': detalles
    })

@login_required
def eliminar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)

    if request.method == 'POST':
        for detalle in venta.detalles.all():
            producto = detalle.producto
            producto.stock += detalle.cantidad
            producto.save()

        venta.delete()
        messages.success(request, f"La venta #{id} fue eliminada y el stock fue restaurado correctamente.")
        return redirect('listar_ventas')

    return render(request, 'productos/eliminar_venta.html', {'venta': venta})

@login_required
@permission_required('auth.view_user', raise_exception=True)
def usuarios_list(request):
    usuarios = User.objects.order_by('username')
    return render(request, 'productos/usuarios_list.html', {'usuarios': usuarios})

@login_required
@permission_required('auth.add_user', raise_exception=True)
def usuario_create(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = request.POST.get("email", "")
            user.first_name = request.POST.get("first_name", "")
            user.last_name = request.POST.get("last_name", "")
            user.is_staff = bool(request.POST.get("is_staff"))
            user.is_active = bool(request.POST.get("is_active", True))
            user.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect('usuarios_list')
    else:
        form = UserCreationForm()
    return render(request, 'productos/usuario_form.html', {
        'form': form,
        'titulo': 'Crear usuario',
        'es_creacion': True,  
    })

UserEditInlineForm = modelform_factory(
    User,
    fields=["first_name", "last_name", "email", "is_staff", "is_active"]
)

@login_required
@permission_required('auth.change_user', raise_exception=True)
def usuario_edit(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserEditInlineForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('usuarios_list')
    else:
        form = UserEditInlineForm(instance=usuario)
    return render(request, 'productos/usuario_form.html', {
        'form': form,
        'titulo': f'Editar usuario: {usuario.username}',
        'es_creacion': False,
    })

@login_required
@permission_required('auth.change_user', raise_exception=True)
def usuario_password(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = PasswordChangeForm(usuario, request.POST)
        if form.is_valid():
            u = form.save()
            if usuario == request.user:  
                update_session_auth_hash(request, u)
            messages.success(request, "Contraseña actualizada correctamente.")
            return redirect('usuarios_list')
    else:
        form = PasswordChangeForm(usuario)
    return render(request, 'productos/usuario_password.html', {
        'form': form,
        'usuario': usuario
    })

@login_required
def dashboard(request):
    hoy = timezone.now()
    year = hoy.year

    ventas_year = Venta.objects.filter(fecha__year=year)
    ventas_year_total = ventas_year.aggregate(total=Sum('total'))['total'] or 0
    facturas_emitidas = ventas_year.count()

    ventas_mensuales_qs = (
        ventas_year
        .annotate(m=TruncMonth('fecha'))
        .values('m')
        .annotate(total=Sum('total'))
        .order_by('m')
    )
    labels = [v['m'].strftime('%b') for v in ventas_mensuales_qs]
    data = [int(v['total'] or 0) for v in ventas_mensuales_qs]

    inventario_neto = (
        Producto.objects
        .annotate(valor=ExpressionWrapper(F('stock') * F('costo'), output_field=DecimalField()))
        .aggregate(total=Sum('valor'))['total'] or 0
    )

    ultimas_ventas = Venta.objects.select_related('usuario').order_by('-fecha')[:8]
    top_productos = (
        DetalleVenta.objects
        .values('producto__nombre')
        .annotate(cantidad=Sum('cantidad'), total=Sum('subtotal'))
        .order_by('-total')[:5]
    )
    bajo_stock = Producto.objects.filter(stock__lte=5).order_by('stock', 'nombre')[:5]
    nuevos_productos = Producto.objects.order_by('-id')[:5]  

    ctx = {
        'year': year,
        'inventario_neto': inventario_neto,
        'ventas_year_total': ventas_year_total,
        'facturas_emitidas': facturas_emitidas,
        'labels': labels, 'data': data,
        'ultimas_ventas': ultimas_ventas,
        'top_productos': top_productos,
        'bajo_stock': bajo_stock,
        'nuevos_productos': nuevos_productos,
    }
    return render(request, 'productos/dashboard.html', ctx)