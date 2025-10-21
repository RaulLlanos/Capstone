from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer

# Permisos: permitir a técnico POST (crear) + lectura; admin full
from core.permissions import AdminOrSuperuserFull_TechReadAndPost as TechCanPost


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    """
    - Técnico: lectura + puede CREAR auditorías (p. ej. con fotos), pero solo listará las
      asociadas a asignaciones donde él es 'asignado_a'.
    - Admin: CRUD completo.

    Filtros:
      - customer_status=AUTORIZA|SIN_MORADORES|RECHAZA|CONTINGENCIA|MASIVO|REAGENDA
      - asignacion__asignado_a=<id>  (filtrar por técnico)
      - asignacion__comuna=<str>, asignacion__zona=<ZONA>
      - created_at__gte=YYYY-MM-DD, created_at__lte=YYYY-MM-DD

    Búsqueda:
      - direccion, rut, comuna

    Orden:
      - -created_at (default), created_at, asignacion__comuna, asignacion__zona
    """
    queryset = (
        AuditoriaVisita.objects
        .select_related("asignacion", "tecnico")
        .all()
        .order_by("-created_at", "-id")
    )
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [permissions.IsAuthenticated, TechCanPost]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "customer_status": ["exact", "in"],
        "asignacion__asignado_a": ["exact"],   # técnico
        "asignacion__comuna": ["exact"],
        "asignacion__zona": ["exact"],
        "created_at": ["gte", "lte"],
    }
    search_fields = [
        "asignacion__direccion",
        "asignacion__rut_cliente",
        "asignacion__comuna",
    ]
    ordering_fields = ["created_at", "asignacion__comuna", "asignacion__zona"]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        # Si es técnico, solo ve auditorías de sus asignaciones
        if getattr(u, "rol", None) == "tecnico":
            qs = qs.filter(asignacion__asignado_a=u.id)
        # preset opcional
        preset = self.request.query_params.get("preset", "")
        if preset == "completadas_rechazadas":
            qs = qs.filter(customer_status__in=[
                "AUTORIZA", "SIN_MORADORES", "RECHAZA", "CONTINGENCIA", "MASIVO"
            ])
        return qs
