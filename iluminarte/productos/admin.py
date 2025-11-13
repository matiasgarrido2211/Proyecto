from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "precio_venta", "costo", "stock", "estado")
    search_fields = ("nombre", "codigo")
   
