# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class AdminAuditorFull_TechReadOnly(BasePermission):
    """
    - Admin/Auditor: full access
    - Técnico: solo lectura (GET/HEAD/OPTIONS)
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not (u and u.is_authenticated):
            return False
        rol = getattr(u, "rol", None)
        if rol in ("admin", "auditor"):
            return True
        if rol == "tecnico":
            return request.method in SAFE_METHODS
        return False


class AdminAuditorFull_TechReadOnlyPlusActions(BasePermission):
    """
    - Admin/Auditor: full access
    - Técnico: solo lectura + POST en acciones explícitas del viewset.
      El viewset puede declarar:
        tech_allowed_actions = {'asignarme', 'estado_cliente', 'reagendar', 'cerrar'}
      Si no declara, por defecto se permite ese set.
    """
    DEFAULT_ACTIONS = {"asignarme", "estado_cliente", "reagendar", "cerrar"}

    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not (u and u.is_authenticated):
            return False
        rol = getattr(u, "rol", None)
        if rol in ("admin", "auditor"):
            return True
        if rol == "tecnico":
            if request.method in SAFE_METHODS:
                return True
            allowed = getattr(view, "tech_allowed_actions", self.DEFAULT_ACTIONS)
            return request.method == "POST" and getattr(view, "action", None) in allowed
        return False
