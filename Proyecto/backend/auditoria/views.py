# auditoria/views.py
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated  # ← import correcto

from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer


class IsAdminOrTechOwner(permissions.BasePermission):
    """
    - 'administrador': acceso total.
    - 'tecnico': solo auditorías donde es el técnico asignado (auditoria.tecnico_id == user.id)
      o donde la asignación está asignada a él (auditoria.asignacion.asignado_a_id == user.id).
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return False
        return getattr(u, "rol", None) in ("administrador", "tecnico")

    def has_object_permission(self, request, view, obj: AuditoriaVisita):
        rol = getattr(request.user, "rol", None)
        if rol == "administrador":
            return True
        if rol == "tecnico":
            return (
                (obj.tecnico_id == request.user.id) or
                (obj.asignacion and obj.asignacion.asignado_a_id == request.user.id)
            )
        return False


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    """
    CRUD de auditorías.
    - Técnico: sólo las suyas (dueño directo o dueño de la asignación).
    - Administrador: todas.

    Filtros:
      - customer_status
      - asignacion__asignado_a (id técnico)
      - asignacion__comuna, asignacion__zona
      - created_at__gte / __lte
    """
    queryset = (
        AuditoriaVisita.objects
        .select_related("asignacion", "tecnico")
        .all()
        .order_by("-created_at", "-id")
    )
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTechOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "customer_status": ["exact", "in"],
        "asignacion__asignado_a": ["exact"],
        "asignacion__comuna": ["exact"],
        "asignacion__zona": ["exact"],
        "created_at": ["gte", "lte"],
    }
    search_fields = ["asignacion__direccion", "asignacion__rut_cliente", "asignacion__comuna"]
    ordering_fields = ["created_at", "asignacion__comuna", "asignacion__zona"]

    def get_queryset(self):
        u = self.request.user
        rol = getattr(u, "rol", None)

        qs = AuditoriaVisita.objects.all().select_related("asignacion", "tecnico")

        if rol == "administrador":
            return qs

        if rol == "tecnico":
            return qs.filter(
                Q(tecnico_id=u.id) |
                Q(asignacion__asignado_a_id=u.id)
            )

        return qs.none()
