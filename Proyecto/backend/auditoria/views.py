from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer

# Permisos: admin/auditor => CRUD total; técnico => CRUD sólo sobre sus propias asignaciones
class IsAdminAuditorOrTechOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        rol = getattr(request.user, "rol", None)
        if rol in ("admin", "auditor", "tecnico"):
            return True
        return False

    def has_object_permission(self, request, view, obj: AuditoriaVisita):
        rol = getattr(request.user, "rol", None)
        if rol in ("admin", "auditor"):
            return True
        if rol == "tecnico":
            # el técnico sólo puede ver/editar/borrar auditorías de sus asignaciones
            return obj.asignacion and obj.asignacion.asignado_a_id == request.user.id
        return False


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    """
    CRUD de auditorías.
    - Técnico: sólo las suyas (asignación.asignado_a == user.id).
    - Admin/Auditor: todas.
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
    permission_classes = [IsAdminAuditorOrTechOwner]
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
        qs = super().get_queryset()
        u = self.request.user
        if getattr(u, "rol", None) == "tecnico":
            qs = qs.filter(asignacion__asignado_a=u.id)
        preset = self.request.query_params.get("preset", "")
        if preset == "completadas_rechazadas":
            qs = qs.filter(customer_status__in=["AUTORIZA", "SIN_MORADORES", "RECHAZA", "CONTINGENCIA", "MASIVO"])
        return qs
