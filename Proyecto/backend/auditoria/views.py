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
    Admin/Auditor: CRUD completo.
    Técnico: solo GET/HEAD/OPTIONS y POST (crear auditoría o subir fotos de su propia asignación).
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not (u and u.is_authenticated):
            return False
        rol = getattr(u, "rol", None)
        if rol in ("admin", "auditor"):
            return True
        if rol == "tecnico":
            return request.method in (*SAFE_METHODS, "POST")
        return False


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    queryset = AuditoriaVisita.objects.all().select_related('asignacion').order_by('-created_at')
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [IsAuthenticated, MixedRolePolicy]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filterset_fields = ['asignacion', 'estado_cliente', 'marca', 'tecnologia']
    search_fields = ['direccion_cliente', 'rut_cliente', 'id_vivienda', 'nombre_auditor']

    def perform_create(self, serializer):
        # El serializer.validate() asegura que, si es técnico, la asignación es suya.
        serializer.save()

    @action(detail=True, methods=['post'], url_path='upload_fotos')
    def upload_fotos(self, request, pk=None):
        obj = self.get_object()
        u = request.user

        if getattr(u, 'rol', None) == 'tecnico' and obj.asignacion.asignado_a_id != u.id:
            return Response({'detail': 'No autorizado.'}, status=403)

        f1 = request.FILES.get('foto_1')
        f2 = request.FILES.get('foto_2')
        f3 = request.FILES.get('foto_3')

        if not any([f1, f2, f3]):
            return Response({'detail': 'Sube al menos una foto (foto_1/foto_2/foto_3).'}, status=400)

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
    Admin/Auditor: CRUD completo.
    Técnico: lectura y creación de issues ligados a auditorías de SU asignación.
    """
    queryset = Issue.objects.all().order_by('id')
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated, MixedRolePolicy]
    filterset_fields = ['auditoria', 'servicio']
    search_fields = ['servicio', 'detalle']
