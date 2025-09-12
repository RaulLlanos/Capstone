# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

def _is_auditor(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "rol", None) == "auditor")

class AdminAuditorFull_TechReadOnly(BasePermission):
    """
    - Auditor: acceso total (CRUD).
    - Técnico: solo lectura (GET/HEAD/OPTIONS).
    - No se considera is_superuser aquí.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_auditor(user):
            return True
        if getattr(user, "rol", None) == "tecnico":
            return request.method in SAFE_METHODS
        return False

class AdminAuditorFull_TechReadOnlyPlusActions(BasePermission):
    """
    - Auditor: acceso total (CRUD).
    - Técnico: lectura + POST en acciones explícitas del ViewSet.
      El ViewSet puede declarar:
          tech_allowed_actions = {'asignarme', 'estado_cliente', 'reagendar', 'cerrar'}
      Si no declara, se usa DEFAULT_ACTIONS.
    - No se considera is_superuser aquí.
    """
    DEFAULT_ACTIONS = {"asignarme", "estado_cliente", "reagendar", "cerrar"}

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_auditor(user):
            return True
        if getattr(user, "rol", None) == "tecnico":
            if request.method in SAFE_METHODS:
                return True
            allowed = getattr(view, "tech_allowed_actions", self.DEFAULT_ACTIONS)
            return (request.method == "POST") and (getattr(view, "action", None) in allowed)
        return False

class AuditorOrSuperuserFull_TechReadAndPost(BasePermission):
    """
    (Nombre legado; funcionalmente SOLO auditor y técnico)
    - Auditor: CRUD completo.
    - Técnico: lectura y POST (crear lo que le corresponda; la 'propiedad' se valida en la vista/serializer).
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_auditor(user):
            return True
        if getattr(user, "rol", None) == "tecnico":
            return (request.method in SAFE_METHODS) or (request.method == "POST")
        return False

class TechOwnsObjectOrAdmin(BasePermission):
    """
    Reforzador opcional de 'propiedad' a nivel objeto:
    - Auditor: siempre True.
    - Técnico: True SOLO si el objeto le pertenece (obj.tecnico_id o obj.asignacion.tecnico_id).
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if _is_auditor(user):
            return True
        if getattr(user, "rol", None) != "tecnico":
            return False
        if request.method in SAFE_METHODS:
            return True
        owner_id = getattr(obj, "tecnico_id", None)
        if owner_id is None and hasattr(obj, "asignacion"):
            owner_id = getattr(getattr(obj, "asignacion", None), "tecnico_id", None)
        return owner_id == getattr(user, "id", None)
