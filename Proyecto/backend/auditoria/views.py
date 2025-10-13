from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer
from core.permissions import AdminAuditorFull_TechReadOnly  # alias existente

class AuditoriaVisitaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - Técnico: ve sus propias auditorías (vinculadas a sus asignaciones).
    - Administrador: ve todas.
    Filtros:
      - estado_cliente=autoriza,sin_moradores,rechaza,contingencia,masivo,reagendo
      - asignacion__asignado_a=<id>  (tecnico_id)
      - asignacion__comuna=<str>, asignacion__zona=<NORTE|CENTRO|SUR>
      - created_at__gte=YYYY-MM-DD, created_at__lte=YYYY-MM-DD
    Ordenamiento: -created_at (default)
    """
    queryset = (
        AuditoriaVisita.objects
        .select_related("asignacion", "tecnico")
        .all()
        .order_by("-created_at")
    )
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [permissions.IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "estado_cliente": ["exact", "in"],
        "asignacion__asignado_a": ["exact"],   # tecnico_id
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
            qs = qs.filter(estado_cliente__in=["autoriza","sin_moradores","rechaza","contingencia","masivo"])
        return qs
