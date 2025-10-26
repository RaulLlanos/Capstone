# core/views_admin.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from core.permissions import AdminOnly
from .models import Configuracion, LogSistema
from .serializers import ConfiguracionSerializer, LogSistemaSerializer

class ConfiguracionAdminViewSet(viewsets.ModelViewSet):
    """
    CRUD: /api/admin/configuracion/
    Solo administrador.
    """
    permission_classes = [IsAuthenticated, AdminOnly]
    queryset = Configuracion.objects.all().order_by("clave")
    serializer_class = ConfiguracionSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {"tipo": ["exact"]}
    search_fields = ["clave", "valor", "descripcion"]
    ordering_fields = ["clave", "updated_at", "created_at"]

    def perform_create(self, serializer):
        obj = serializer.save()
        LogSistema.objects.create(
            usuario=self.request.user,
            accion=LogSistema.Accion.CONFIG_CREATE,
            detalle=f"Creada config '{obj.clave}'={obj.valor}",
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        LogSistema.objects.create(
            usuario=self.request.user,
            accion=LogSistema.Accion.CONFIG_UPDATE,
            detalle=f"Actualizada config '{obj.clave}'={obj.valor}",
        )

    def perform_destroy(self, instance):
        clave = instance.clave
        valor = instance.valor
        super().perform_destroy(instance)
        LogSistema.objects.create(
            usuario=self.request.user,
            accion=LogSistema.Accion.CONFIG_DELETE,
            detalle=f"Eliminada config '{clave}' (valor anterior={valor})",
        )


class LogsAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET: /api/admin/logs/
    Filtros: accion, usuario, created_at__gte/lte, search(detalle)
    Solo administrador.
    """
    permission_classes = [IsAuthenticated, AdminOnly]
    queryset = LogSistema.objects.select_related("usuario").all()
    serializer_class = LogSistemaSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "accion": ["exact", "in"],
        "usuario": ["exact"],
        "created_at": ["gte", "lte"],
    }
    search_fields = ["detalle", "usuario__email"]
    ordering_fields = ["created_at", "id", "accion"]
    ordering = ["-created_at", "-id"]
