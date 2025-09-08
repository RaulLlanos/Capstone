# usuarios/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import AdminAuditorFull_TechReadOnly
from .models import Usuario, Tecnico, Visita, Reagendamiento, HistorialVisita, EvidenciaServicio
from .serializers import (
    UsuarioSerializer, TecnicoSerializer, VisitaSerializer,
    ReagendamientoSerializer, HistorialVisitaSerializer, EvidenciaServicioSerializer
)


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    - Admin/Auditor: CRUD total de usuarios.
    - Técnico: SOLO lectura de su propio usuario.
    """
    queryset = Usuario.objects.all().order_by('-date_joined')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'rut_usuario']
    ordering_fields = ['date_joined', 'email', 'first_name', 'last_name']
    filterset_fields = ['rol', 'is_active', 'is_staff']

    def get_queryset(self):
        u = self.request.user
        if getattr(u, "rol", None) in ("admin", "auditor"):
            return super().get_queryset()
        return Usuario.objects.filter(id=u.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)


class TecnicoViewSet(viewsets.ModelViewSet):
    """
    - Admin/Auditor: CRUD total de técnicos.
    - Técnico: SOLO lectura de su propia ficha.
    """
    queryset = Tecnico.objects.select_related('usuario').all()
    serializer_class = TecnicoSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['usuario__email', 'usuario__first_name', 'usuario__last_name', 'zona']
    ordering_fields = ['id_tecnico', 'zona']
    filterset_fields = ['zona', 'usuario']

    def get_queryset(self):
        u = self.request.user
        if getattr(u, "rol", None) in ("admin", "auditor"):
            return super().get_queryset()
        return super().get_queryset().filter(usuario=u)


class VisitaViewSet(viewsets.ModelViewSet):
    queryset = Visita.objects.all().order_by('-fecha_creacion')
    serializer_class = VisitaSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['cliente_nombre', 'cliente_apellido', 'cliente_direccion', 'cliente_comuna', 'cliente_telefono']
    filterset_fields = ['tecnico', 'estado', 'tipo_servicio', 'fecha_programada']


class ReagendamientoViewSet(viewsets.ModelViewSet):
    queryset = Reagendamiento.objects.all().order_by('-fecha_hora')
    serializer_class = ReagendamientoSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['motivo']
    filterset_fields = ['visita', 'usuario', 'fecha_nueva', 'hora_nueva']


class HistorialVisitaViewSet(viewsets.ModelViewSet):
    queryset = HistorialVisita.objects.all().order_by('-fecha_hora')
    serializer_class = HistorialVisitaSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['accion', 'detalles']
    filterset_fields = ['visita', 'usuario', 'accion']


class EvidenciaServicioViewSet(viewsets.ModelViewSet):
    queryset = EvidenciaServicio.objects.all().order_by('-fecha_hora')
    serializer_class = EvidenciaServicioSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['descripcion', 'tipo_evidencia', 'archivo_ruta']
    filterset_fields = ['visita', 'usuario', 'tipo_evidencia']
