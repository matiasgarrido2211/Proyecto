from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=0)
    costo = models.DecimalField(max_digits=10, decimal_places=0)
    stock = models.IntegerField()
    foto = models.ImageField(upload_to="productos/", blank=True, null=True)

    @property
    def estado(self):
        return "Activo" if self.stock > 0 else "Inactivo"

    def __str__(self):
        return f"{self.nombre} - {self.codigo} ({self.estado})"


class Venta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y')}"

    def calcular_total(self):
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total = total
        self.save()
        return total


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

