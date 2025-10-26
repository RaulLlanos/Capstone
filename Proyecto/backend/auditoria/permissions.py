# auditoria/permissions.py
from rest_framework import permissions

class IsAdminOrTechOwner(permissions.BasePermission):
    """
    Admin: acceso total.
    Técnico: solo puede ver/editar si:
      - es el técnico asignado en la auditoría (auditoria.tecnico_id == user.id), o
      - la asignación ligada está/estuvo asignada a él (auditoria.asignacion.asignado_a_id == user.id)
    """

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        return getattr(u, "rol", None) in ("administrador", "tecnico")

    def has_object_permission(self, request, view, obj):
        u = request.user
        rol = getattr(u, "rol", None)

        if rol == "administrador":
            return True

        if rol == "tecnico":
            # dueñ@ por cualquiera de los dos criterios
            if getattr(obj, "tecnico_id", None) == u.id:
                return True
            asignacion = getattr(obj, "asignacion", None)
            return bool(asignacion and getattr(asignacion, "asignado_a_id", None) == u.id)

        return False
