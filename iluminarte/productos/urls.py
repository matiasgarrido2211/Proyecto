from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.dashboard, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("productos/", views.home_view, name="productos_list"), 
    path("agregar/", views.agregar_producto, name="agregar_producto"),
    path("modificar/<int:producto_id>/", views.modificar_producto, name="modificar_producto"),
    path("eliminar/<int:producto_id>/", views.eliminar_producto, name="eliminar_producto"),
    path('registrar_venta/', views.registrar_venta, name='registrar_venta'),
    path('listar_ventas/', views.listar_ventas, name='listar_ventas'),
    path('modificar_venta/<int:id>/', views.modificar_venta, name='modificar_venta'),
    path('eliminar_venta/<int:id>/', views.eliminar_venta, name='eliminar_venta'),
    path('usuarios_list/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:user_id>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:user_id>/password/', views.usuario_password, name='usuario_password'),
]