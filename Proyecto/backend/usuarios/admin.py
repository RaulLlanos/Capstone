from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import Usuario
# Register your models here.

class UsuarioAdminPersonalizado(UserAdmin):
    # Configuración básica
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'rol', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('rol', 'is_staff', 'is_active')
    
    # FIELDSETS personalizados (¡sin username!)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'rut_usuario')}),
        ('Permisos', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    # ADD_FIELDSETS personalizados (¡sin username!)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'rut_usuario', 'rol', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    # Eliminar cualquier referencia a username
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Asegurar que no se intente usar username
        if 'username' in form.base_fields:
            del form.base_fields['username']
        return form

admin.site.register(Usuario, UsuarioAdminPersonalizado)