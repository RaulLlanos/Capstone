# auditoria/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import AuditoriaVisita, Issue
from .serializers import AuditoriaVisitaSerializer, IssueSerializer


class MixedRolePolicy(BasePermission):
    """
    Permisos:
    - Admin/Auditor: CRUD total.
    - Técnico: SOLO lectura (GET/HEAD/OPTIONS) + POST para:
        * crear auditoría (cuando el cliente autoriza)  -> POST /api/auditorias/
        * subir fotos a su propia auditoría             -> POST /api/auditorias/{id}/upload_fotos
      NO puede actualizar (PUT/PATCH) ni borrar (DELETE).
    """
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False

        # Admin/Auditor: todo
        if getattr(u, 'rol', None) in ('admin', 'auditor'):
            return True

        # Técnico:
        if getattr(u, 'rol', None) == 'tecnico':
            if request.method in SAFE_METHODS:
                return True
            # permitir SOLO creación de auditoría (POST) y acciones POST específicas
            action = getattr(view, 'action', None)
            if request.method == 'POST':
                # en ViewSet de auditoría, POST sin detail es "create"
                # y en detail action de fotos es "upload_fotos"
                return (action is None and view.action == 'create') or (action == 'upload_fotos')
        return False

    def has_object_permission(self, request, view, obj):
        u = request.user
        if getattr(u, 'rol', None) in ('admin', 'auditor'):
            return True
        if request.method in SAFE_METHODS:
            return True

        # Técnico: solo upload_fotos sobre SU propia asignación
        action = getattr(view, 'action', None)
        if getattr(u, 'rol', None) == 'tecnico' and action == 'upload_fotos':
            return obj.asignacion.asignado_a_id == u.id
        return False


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    queryset = (AuditoriaVisita.objects
                .all()
                .select_related('asignacion')
                .order_by('-created_at'))
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [IsAuthenticated, MixedRolePolicy]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filterset_fields = ['asignacion', 'estado_cliente', 'marca', 'tecnologia']
    search_fields = ['direccion_cliente', 'rut_cliente', 'id_vivienda', 'nombre_auditor']

    def create(self, request, *args, **kwargs):
        """
        Técnicos pueden CREAR auditorías SOLO de su propia asignación.
        El serializer ya valida esto (revisa asignacion.asignado_a == request.user).
        Admin/Auditor pueden crear libremente.
        """
        return super().create(request, *args, **kwargs)

    # Bloqueos para técnicos: no pueden editar ni borrar
    def update(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para modificar auditorías.'}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para modificar auditorías.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para borrar auditorías.'}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='upload_fotos')
    def upload_fotos(self, request, pk=None):
        """
        Subir 1-3 fotos (foto_1 / foto_2 / foto_3).
        - Técnico: solo si la asignación le pertenece.
        - Admin/Auditor: libre.
        """
        obj = self.get_object()
        u = request.user

        if getattr(u, 'rol', None) == 'tecnico' and obj.asignacion.asignado_a_id != u.id:
            return Response({'detail': 'No autorizado.'}, status=403)

        f1 = request.FILES.get('foto_1')
        f2 = request.FILES.get('foto_2')
        f3 = request.FILES.get('foto_3')

        if not any([f1, f2, f3]):
            return Response({'detail': 'Sube al menos una foto (foto_1/foto_2/foto_3).'}, status=400)

        # Validación de tipo y tamaño (10MB)
        for f in (f1, f2, f3):
            if f:
                if not getattr(f, 'content_type', '').startswith('image/'):
                    return Response({'detail': 'Solo imágenes.'}, status=400)
                if f.size > 10 * 1024 * 1024:
                    return Response({'detail': 'Máx 10MB por foto.'}, status=400)

        if f1: obj.foto_1 = f1
        if f2: obj.foto_2 = f2
        if f3: obj.foto_3 = f3
        obj.save()

        return Response(AuditoriaVisitaSerializer(obj, context={'request': request}).data, status=200)


class IssueViewSet(viewsets.ModelViewSet):
    """
    - Admin/Auditor: CRUD total de issues.
    - Técnico: SOLO lectura. (Los issues los puede mandar anidados al crear la auditoría).
    """
    queryset = Issue.objects.all().order_by('-id')
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, MixedRolePolicy]

    def create(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para crear issues aquí.'}, status=403)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para modificar issues.'}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para modificar issues.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if getattr(request.user, 'rol', None) == 'tecnico':
            return Response({'detail': 'No autorizado para borrar issues.'}, status=403)
        return super().destroy(request, *args, **kwargs)
