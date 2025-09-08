# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

def is_admin_or_auditor(user):
    return getattr(user, "rol", None) in ("admin", "auditor")

class AdminAuditorFull_TechReadOnly(BasePermission):
    """
    - Admin/Auditor: CRUD total.
    - Técnico: SOLO lectura (GET/HEAD/OPTIONS).
    """
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if is_admin_or_auditor(u):
            return True
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        u = request.user
        if is_admin_or_auditor(u):
            return True
        return request.method in SAFE_METHODS


class AdminAuditorFull_TechReadOnlyPlusActions(BasePermission):
    """
    Para Asignaciones:
    - Admin/Auditor: CRUD total.
    - Técnico: lectura + acciones POST específicas (asignarme, reagendar, cerrar).
    """
    allowed_actions_for_tech = {"asignarme", "reagendar", "cerrar"}

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if is_admin_or_auditor(u):
            return True

        if request.method in SAFE_METHODS:
            return True

        # Permitir acciones custom concretas
        action = getattr(view, "action", None)
        return request.method == "POST" and action in self.allowed_actions_for_tech

    def has_object_permission(self, request, view, obj):
        u = request.user
        if is_admin_or_auditor(u):
            return True

        if request.method in SAFE_METHODS:
            return True

        # Para acciones custom, validamos ownership donde aplique en la vista
        action = getattr(view, "action", None)
        return request.method == "POST" and action in self.allowed_actions_for_tech
