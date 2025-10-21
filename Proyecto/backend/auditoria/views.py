from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer
from core.permissions import AdminOrSuperuserFull_TechCrudOwn


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    """
    - ADMIN: CRUD total.
    - TÉCNICO: CRUD restringido a sus asignaciones (propias).
      * create: solo si 'asignacion.asignado_a' == técnico
      * retrieve/list: solo ve las suyas
      * update/delete: solo sobre las suyas
    """
    queryset = (AuditoriaVisita.objects
                .select_related("asignacion", "tecnico")
                .all()
                .order_by("-created_at"))
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [permissions.IsAuthenticated, AdminOrSuperuserFull_TechCrudOwn]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "customer_status": ["exact", "in"],
        "asignacion__asignado_a": ["exact"],  # filtra por técnico
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
            qs = qs.filter(asignacion__asignado_a_id=u.id)
        return qs
