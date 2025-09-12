from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from core.permissions import AuditorOrSuperuserFull_TechReadAndPost
from .models import Auditoria, EvidenciaServicio
from .serializers import AuditoriaSerializer, EvidenciaServicioSerializer

class AuditoriaViewSet(viewsets.ModelViewSet):
    queryset = Auditoria.objects.select_related("asignacion").order_by("-created_at")
    serializer_class = AuditoriaSerializer
    permission_classes = [IsAuthenticated, AuditorOrSuperuserFull_TechReadAndPost]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filterset_fields = ("asignacion", "estado_cliente", "marca", "tecnologia")
    search_fields = ("direccion_cliente", "rut_cliente", "id_vivienda")

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"], url_path="upload_fotos", parser_classes=[MultiPartParser, FormParser])
    def upload_fotos(self, request, pk=None):
        auditoria = self.get_object()
        u = request.user
        asignacion = auditoria.asignacion

        # Técnicos: solo si es su asignación
        if getattr(u, "rol", None) == "tecnico" and asignacion.asignado_a_id != u.id:
            return Response({"detail": "No autorizado."}, status=403)

        files = [request.FILES.get("foto_1"), request.FILES.get("foto_2"), request.FILES.get("foto_3")]
        files = [f for f in files if f]
        if not files:
            return Response({"detail": "Sube al menos una foto (foto_1/foto_2/foto_3)."}, status=400)

        for f in files:
            if not getattr(f, "content_type", "").startswith("image/"):
                return Response({"detail": "Solo imágenes."}, status=400)
            if f.size > 10 * 1024 * 1024:
                return Response({"detail": "Máximo 10MB por imagen."}, status=400)

        created = []
        for f in files:
            ev = EvidenciaServicio.objects.create(
                auditoria=auditoria,
                asignacion=asignacion,
                archivo=f,
                usuario=u
            )
            created.append(ev)

        return Response(EvidenciaServicioSerializer(created, many=True, context={"request": request}).data, status=201)
