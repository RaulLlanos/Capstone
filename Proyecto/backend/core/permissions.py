# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

def _is_admin(user) -> bool:
    """
    Verdadero si el usuario autenticado tiene rol 'administrador'.
    """
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "rol", None) == "administrador"
    )


# ========================
# Nombres nuevos (claros)
# ========================

class AdminFull_TechReadOnly(BasePermission):
    """
    - Administrador: acceso total (CRUD).
    - Técnico: solo lectura (GET/HEAD/OPTIONS).
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_admin(user):
            return True
        if getattr(user, "rol", None) == "tecnico":
            return request.method in SAFE_METHODS
        return False


class AdminFull_TechReadOnlyPlusActions(BasePermission):
    """
    - Administrador: acceso total (CRUD).
    - Técnico: lectura + POST en acciones explícitas del ViewSet.
      El ViewSet puede declarar:
          tech_allowed_actions = {'asignarme', 'estado_cliente', 'reagendar', 'cerrar'}
      Si no declara, se usa DEFAULT_ACTIONS.
    """
    DEFAULT_ACTIONS = {"asignarme", "estado_cliente", "reagendar", "cerrar"}

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_admin(user):
            return True
        if getattr(user, "rol", None) == "tecnico":
            if request.method in SAFE_METHODS:
                return True
            allowed = getattr(view, "tech_allowed_actions", self.DEFAULT_ACTIONS)
            return (request.method == "POST") and (getattr(view, "action", None) in allowed)
        return False


class AdminOrSuperuserFull_TechReadAndPost(BasePermission):
    """
    - Administrador (o superuser en /admin/): CRUD completo.
    - Técnico: lectura y POST (crear lo que le corresponda; la 'propiedad' se valida en la vista/serializer).
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_admin(user) or getattr(user, "is_superuser", False):
            return True
        if getattr(user, "rol", None) == "tecnico":
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
        if getattr(user, "rol", None) != "tecnico":
            return False
        if request.method in SAFE_METHODS:
            return True
        owner_id = getattr(obj, "tecnico_id", None)
        if owner_id is None and hasattr(obj, "asignacion"):
            owner_id = getattr(getattr(obj, "asignacion", None), "tecnico_id", None)
        return owner_id == getattr(user, "id", None)


# ======================================================
# Alias de compatibilidad (no rompen tu código actual)
# ======================================================
# Los nombres antiguos quedan como alias a los nuevos,
# para que tus imports existentes sigan funcionando.
AdminAuditorFull_TechReadOnly = AdminFull_TechReadOnly
AdminAuditorFull_TechReadOnlyPlusActions = AdminFull_TechReadOnlyPlusActions
AuditorOrSuperuserFull_TechReadAndPost = AdminOrSuperuserFull_TechReadAndPost
