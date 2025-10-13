from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdminPersonalizado(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "rol", "rut", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("rol", "is_active", "is_staff")

    # Sin username
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "rut_num", "dv")}),
        ("Permisos", {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2",
                "first_name", "last_name",
                "rut_num", "dv",
                "rol", "is_active", "is_staff", "is_superuser",
            ),
        }),
    )

    # Quita "username" si alguna clase base intenta mostrarlo
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields.pop("username", None)
        return form

# Ocultar "Grupos" si no lo usarán
from django.contrib.auth.models import Group
try:
    admin.site.unregister(Group)
except Exception:
    pass
