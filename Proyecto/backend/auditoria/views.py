# auditoria/views.py
from rest_framework import viewsets, permissions
from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer
from core.permissions import AdminAuditorFull_TechReadOnly  # o tu clase renombrada a AdminFull...

class AuditoriaVisitaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - Técnico: ve sus propias auditorías (vinculadas a sus asignaciones).
    - Administrador: ve todas.
    """
    queryset = AuditoriaVisita.objects.select_related("asignacion").all().order_by("-created_at")
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [permissions.IsAuthenticated, AdminAuditorFull_TechReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if getattr(u, "rol", None) == "tecnico":
            return qs.filter(asignacion__asignado_a=u.id)
        return qs
