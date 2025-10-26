# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

# === Helpers ===
def _is_admin(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "rol", None) == "administrador")

def _is_tech(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "rol", None) == "tecnico")

# === Nombres “limpios” ===
class AdminFull_TechReadOnly(BasePermission):
    """
    - Administrador: CRUD completo.
    - Técnico: solo lectura.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_admin(user):
            return True
        if _is_tech(user):
            return request.method in SAFE_METHODS
        return False


class AdminFull_TechReadOnlyPlusActions(BasePermission):
    """
    - Administrador: CRUD completo.
    - Técnico: lectura + POST/PATCH en acciones explícitas del ViewSet.
      El ViewSet puede declarar:
          tech_allowed_actions = {'asignarme','estado_cliente','reagendar','cerrar','partial_update', ...}
      Si no declara, se usa DEFAULT_ACTIONS.
    """
    DEFAULT_ACTIONS = {
        # acciones declaradas con @action
        "asignarme", "estado_cliente", "reagendar", "cerrar",
        "historial", "historial_export",
        "metrics_resumen", "metrics_tecnico", "metrics_serie", "metrics_export",
        "export_metricas_get",
        # acciones “built-in” de DRF
        "partial_update",  # PATCH /{id}/
    }

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if _is_admin(user):
            return True

        if _is_tech(user):
            # Lectura siempre permitida
            if request.method in SAFE_METHODS:
                return True

            action = getattr(view, "action", None)
            allowed = getattr(view, "tech_allowed_actions", self.DEFAULT_ACTIONS)

            # Permitimos POST y PATCH en acciones específicas (incluye partial_update)
            if request.method in {"POST", "PATCH"} and (action in allowed or action == "partial_update"):
                return True

            return False

        return False


class AdminOrSuperuserFull_TechReadAndPost(BasePermission):
    """
    - Administrador (o is_superuser): CRUD completo.
    - Técnico: lectura y POST (la 'propiedad' se valida en vista/serializer).
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_admin(user) or getattr(user, "is_superuser", False):
            return True
        if _is_tech(user):
            return (request.method in SAFE_METHODS) or (request.method == "POST")
        return False


class TechOwnsObjectOrAdmin(BasePermission):
    """
    - Administrador: siempre True.
    - Técnico: True SOLO si el objeto le pertenece (obj.tecnico_id o obj.asignacion.tecnico_id).
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_admin(user):
            return True
        if not _is_tech(user):
            return False
        if request.method in SAFE_METHODS:
            return True
        owner_id = getattr(obj, "tecnico_id", None)
        if owner_id is None and hasattr(obj, "asignacion"):
            owner_id = getattr(getattr(obj, "asignacion", None), "tecnico_id", None)
        return owner_id == getattr(user, "id", None)
    

class AdminOrSuperuserFull_TechCrudOwn(BasePermission):
    """
    - Admin / superuser: CRUD total.
    - Técnico: CRUD pero solo sobre objetos propios:
        * auditoría.tecnico_id == user.id
        * o la asignación de esa auditoría pertenece al técnico (asignacion.asignado_a_id == user.id)
      (Para 'create' validamos que la asignación sea suya.)
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return False
        if _is_admin(user) or getattr(user, "is_superuser", False):
            return True
        if _is_tech(user):
            # Permitimos todos los métodos; en detalle se filtra con has_object_permission.
            return True
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if _is_admin(user) or getattr(user, "is_superuser", False):
            return True
        if not _is_tech(user):
            return False
        owner_id = getattr(obj, "tecnico_id", None)
        if owner_id is None and hasattr(obj, "asignacion"):
            owner_id = getattr(getattr(obj, "asignacion", None), "asignado_a_id", None)
        return owner_id == getattr(user, "id", None)
    

class AdminOnly(BasePermission):
    """Solo permite acceso a usuarios con rol=administrador."""
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        return bool(u and getattr(u, "is_authenticated", False) and getattr(u, "rol", None) == "administrador")



# === Alias retrocompatibles (si algo del proyecto viejo los importaba) ===
AdminAuditorFull_TechReadOnly = AdminFull_TechReadOnly
AdminAuditorFull_TechReadOnlyPlusActions = AdminFull_TechReadOnlyPlusActions
AuditorOrSuperuserFull_TechReadAndPost = AdminOrSuperuserFull_TechReadAndPost
