# asignaciones/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from django.db import transaction
from django.utils.dateparse import parse_date
import csv, io

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, OpenApiExample,
)

from .models import DireccionAsignada, EstadoAsignacion
from .serializers import DireccionAsignadaSerializer
from usuarios.models import Usuario


class MixedRolePolicy(BasePermission):
    """Admin/Auditor: full CRUD. Técnico: solo lectura + acciones puntuales."""
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False

        if getattr(u, 'rol', None) in ('admin', 'auditor'):
            return True

        if getattr(u, 'rol', None) == 'tecnico':
            # lectura siempre
            if request.method in SAFE_METHODS:
                return True
            # permitir solo ciertas POST de acciones custom del viewset
            allowed_actions = {'asignarme', 'reagendar', 'cerrar'}
            if request.method == 'POST' and getattr(view, 'action', None) in allowed_actions:
                return True
            # NO permitir create/update/delete ni otras acciones
            return False

        return False


@extend_schema_view(
    list=extend_schema(
        summary="Listar asignaciones",
        description="Lista paginada y filtrable de direcciones asignadas.",
        parameters=[
            OpenApiParameter("marca", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("tecnologia", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("encuesta", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("asignado_a", OpenApiTypes.INT, OpenApiParameter.QUERY),
            OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("rut_cliente", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("id_vivienda", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("reagendado_fecha", OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter("reagendado_bloque", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description="Busca en dirección, RUT, id_vivienda, id_qualtrics"),
        ],
        responses=DireccionAsignadaSerializer,
    ),
    retrieve=extend_schema(
        summary="Detalle de asignación",
        responses=DireccionAsignadaSerializer,
    ),
    create=extend_schema(
        summary="Crear asignación (solo Admin/Auditor)",
        description="Crea una asignación. Técnicos no pueden usar este endpoint.",
        responses=DireccionAsignadaSerializer,
    ),
)
class DireccionAsignadaViewSet(viewsets.ModelViewSet):
    queryset = DireccionAsignada.objects.all().order_by('-created_at')
    serializer_class = DireccionAsignadaSerializer
    permission_classes = [IsAuthenticated & MixedRolePolicy]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    filterset_fields = [
        'marca', 'tecnologia', 'encuesta', 'asignado_a', 'estado',
        'rut_cliente', 'id_vivienda',
        'reagendado_fecha', 'reagendado_bloque',  # filtros de reagendamiento
    ]
    search_fields = ['direccion', 'rut_cliente', 'id_vivienda', 'id_qualtrics']

    @extend_schema(
        summary="Asignarme una dirección (técnico)",
        description="El técnico autenticado se asigna la dirección si está PENDIENTE.",
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=True, methods=['post'])
    def asignarme(self, request, pk=None):
        registro = self.get_object()
        if request.user.rol != 'tecnico':
            return Response({'detail': 'Solo técnicos pueden asignarse direcciones.'}, status=403)
        if registro.estado != EstadoAsignacion.PENDIENTE:
            return Response({'detail': 'La dirección no está disponible.'}, status=400)
        registro.asignado_a = request.user
        registro.estado = EstadoAsignacion.ASIGNADA
        registro.save(update_fields=['asignado_a', 'estado', 'updated_at'])
        return Response(self.get_serializer(registro).data)

    @extend_schema(
        summary="Carga masiva (CSV) (Admin/Auditor)",
        description=(
            "Sube un CSV UTF-8 con los encabezados: "
            "`fecha, tecnologia, marca, rut_cliente, id_vivienda, direccion, encuesta, id_qualtrics`."
        ),
        examples=[
            OpenApiExample(
                'CSV esperado',
                description='Contenido ejemplo (2 filas)',
                value=(
                    "fecha,tecnologia,marca,rut_cliente,id_vivienda,direccion,encuesta,id_qualtrics\n"
                    "2025-09-05,FTTH,CLARO,12.345.678-9,HOME-001,\"Av. Siempre Viva 123, Ñuñoa\",instalacion,QX-001\n"
                    "2025-09-06,HFC,VTR,9.876.543-2,HOME-002,\"Los Olmos 456, Maipú\",post_visita,QX-002\n"
                ),
            )
        ],
        responses={201: {'type': 'object', 'properties': {'created': {'type': 'integer'}}}},
    )
    @action(detail=False, methods=['post'])
    def upload_csv(self, request):
        if request.user.rol not in ('admin', 'auditor'):
            return Response({'detail': 'No autorizado.'}, status=403)

        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Falta archivo CSV en campo "file".'}, status=400)

        # Lee CSV como UTF-8
        try:
            decoded = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response({'detail': 'El CSV debe estar en UTF-8.'}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        required = {'fecha', 'tecnologia', 'marca', 'rut_cliente', 'id_vivienda', 'direccion', 'encuesta'}
        headers = set([h.strip() for h in (reader.fieldnames or [])])
        if not required.issubset(headers):
            return Response({'detail': f'Encabezados requeridos: {sorted(required)}'}, status=400)

        created = 0
        with transaction.atomic():
            for idx, row in enumerate(reader, start=2):  # fila 1 = encabezados
                fecha_str = (row.get('fecha') or '').strip()
                fecha_val = parse_date(fecha_str) if fecha_str else None
                if fecha_str and not fecha_val:
                    return Response(
                        {'detail': f'Fila {idx}: fecha inválida "{fecha_str}" (use YYYY-MM-DD).'},
                        status=400
                    )

                DireccionAsignada.objects.create(
                    fecha=fecha_val,
                    tecnologia=(row['tecnologia'] or '').strip().upper(),
                    marca=(row['marca'] or '').strip().upper(),
                    rut_cliente=(row['rut_cliente'] or '').strip(),
                    id_vivienda=(row['id_vivienda'] or '').strip(),
                    direccion=(row['direccion'] or '').strip(),
                    encuesta=(row['encuesta'] or '').strip(),
                    id_qualtrics=(row.get('id_qualtrics') or '').strip(),
                )
                created += 1

        return Response({'created': created}, status=201)

    @extend_schema(
        summary="Reagendar visita",
        description="Reagenda una visita con **fecha (YYYY-MM-DD)** y **bloque** (10-13 o 14-18).",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'fecha': {'type': 'string', 'format': 'date', 'example': '2025-09-10'},
                    'bloque': {'type': 'string', 'enum': ['10-13', '14-18'], 'example': '10-13'},
                },
                'required': ['fecha', 'bloque'],
            }
        },
        responses=DireccionAsignadaSerializer,
        examples=[
            OpenApiExample(
                'Reagendamiento ejemplo',
                value={'fecha': '2025-09-10', 'bloque': '10-13'}
            )
        ],
    )
    @action(detail=True, methods=['post'], url_path='reagendar')
    def reagendar(self, request, pk=None):
        """Reagendamiento: fecha (YYYY-MM-DD) + bloque (10-13/14-18)."""
        obj = self.get_object()
        u = request.user

        # Permiso: técnico asignado o auditor/admin
        if u.rol == 'tecnico' and obj.asignado_a_id != u.id:
            return Response(
                {'detail': 'Solo el técnico asignado o auditor/admin puede reagendar.'},
                status=403
            )

        fecha_str = (request.data.get('fecha') or '').strip()
        bloque = (request.data.get('bloque') or '').strip()

        if not fecha_str or not bloque:
            return Response(
                {'detail': 'Debe enviar fecha (YYYY-MM-DD) y bloque (10-13/14-18).'},
                status=400
            )

        fecha = parse_date(fecha_str)
        if not fecha:
            return Response({'detail': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)

        if bloque not in ('10-13', '14-18'):
            return Response({'detail': 'Bloque inválido. Use 10-13 o 14-18.'}, status=400)

        obj.reagendado_fecha = fecha
        obj.reagendado_bloque = bloque
        obj.estado = EstadoAsignacion.REAGENDADA
        obj.save(update_fields=['reagendado_fecha', 'reagendado_bloque', 'estado', 'updated_at'])

        return Response(self.get_serializer(obj).data, status=200)

    @extend_schema(
        summary="Prefill para el front",
        description="Devuelve técnicos, cliente, marca/tecnología, opciones de estado y bloques.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'tecnicos': {'type': 'array', 'items': {
                        'type': 'object',
                        'properties': {'id': {'type': 'integer'}, 'nombre': {'type': 'string'}, 'email': {'type': 'string'}}
                    }},
                    'cliente': {'type': 'object', 'properties': {
                        'rut': {'type': 'string'},
                        'id_vivienda': {'type': 'string'},
                        'direccion': {'type': 'string'},
                    }},
                    'marca': {'type': 'string'},
                    'tecnologia': {'type': 'string'},
                    'estado_cliente_choices': {'type': 'array', 'items': {'type': 'object'}},
                    'bloques': {'type': 'array', 'items': {'type': 'object'}},
                }
            }
        }
    )
    @action(detail=True, methods=['get'], url_path='prefill')
    def prefill(self, request, pk=None):
        """Datos para precargar en el front: técnicos, cliente, marca/tecnología, choices."""
        obj = self.get_object()

        tecnicos = list(
            Usuario.objects.filter(rol='tecnico', is_active=True)
            .values('id', 'first_name', 'last_name', 'email')
            .order_by('first_name', 'last_name')
        )

        return Response({
            "tecnicos": [
                {
                    "id": t["id"],
                    "nombre": f'{t["first_name"]} {t["last_name"]}',
                    "email": t["email"],
                } for t in tecnicos
            ],
            "cliente": {
                "rut": obj.rut_cliente,
                "id_vivienda": obj.id_vivienda,
                "direccion": obj.direccion,
            },
            "marca": obj.marca,
            "tecnologia": obj.tecnologia,
            "estado_cliente_choices": [
                {"value": "autoriza", "label": "Autoriza a ingresar"},
                {"value": "sin_moradores", "label": "Sin Moradores"},
                {"value": "rechaza", "label": "Rechaza"},
                {"value": "contingencia", "label": "Contingencia externa"},
                {"value": "masivo", "label": "Incidencia Masivo ClaroVTR"},
                {"value": "reagendo", "label": "Reagendó"}
            ],
            "bloques": [
                {"value": "10-13", "label": "10:00 a 13:00"},
                {"value": "14-18", "label": "14:00 a 18:00"},
            ]
        })

    @extend_schema(
        summary="Cerrar visita sin auditoría",
        description=(
            "Cierra una visita **sin** crear auditoría (cuando Q5 != 'autoriza').\n\n"
            "Body: `{ \"motivo\": \"sin_moradores|rechaza|contingencia|masivo\" }`"
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'motivo': {
                        'type': 'string',
                        'enum': ['sin_moradores', 'rechaza', 'contingencia', 'masivo']
                    }
                },
                'required': ['motivo']
            }
        },
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=True, methods=['post'], url_path='cerrar')
    def cerrar(self, request, pk=None):
        """
        Cierra visita SIN crear auditoría (para Q5 distintos de 'autoriza'):
        body: {"motivo": "sin_moradores|rechaza|contingencia|masivo"}
        """
        obj = self.get_object()
        u = request.user

        # Permiso: técnico asignado o auditor/admin
        if u.rol == 'tecnico' and obj.asignado_a_id != u.id:
            return Response({'detail': 'No autorizado.'}, status=403)

        motivo = (request.data.get('motivo') or '').strip()
        if motivo not in ('sin_moradores', 'rechaza', 'contingencia', 'masivo'):
            return Response(
                {'detail': 'motivo inválido (use: sin_moradores | rechaza | contingencia | masivo).'},
                status=400
            )

        # marca como visitada (ajusta al estado que prefieras)
        obj.estado = EstadoAsignacion.VISITADA
        obj.save(update_fields=['estado', 'updated_at'])

        return Response(self.get_serializer(obj).data, status=200)

    @extend_schema(
        summary="Mis asignaciones (técnico)",
        description="Lista las asignaciones del técnico autenticado.",
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=False, methods=['get'], url_path='mias')
    def mias(self, request):
        u = request.user
        if u.rol != 'tecnico':
            return Response({'detail': 'Solo técnicos.'}, status=403)
        qs = self.get_queryset().filter(asignado_a=u)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)
