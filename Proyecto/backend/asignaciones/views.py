# asignaciones/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from django.db import transaction
from django.utils.dateparse import parse_date
import csv, io

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, OpenApiExample, OpenApiResponse
)

from core.permissions import AdminAuditorFull_TechReadOnlyPlusActions
from .models import DireccionAsignada, EstadoAsignacion
from .serializers import DireccionAsignadaSerializer
from usuarios.models import Usuario


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
    retrieve=extend_schema(summary="Detalle de asignación", responses=DireccionAsignadaSerializer),
    create=extend_schema(summary="Crear asignación (solo Admin/Auditor)", responses=DireccionAsignadaSerializer),
)
class DireccionAsignadaViewSet(viewsets.ModelViewSet):
    """
    - Admin/Auditor: CRUD total + carga CSV
    - Técnico: solo lectura + acciones: asignarme, estado_cliente, reagendar, cerrar
    """
    queryset = DireccionAsignada.objects.all().order_by('-created_at')
    serializer_class = DireccionAsignadaSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnlyPlusActions]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    # define las acciones que puede usar el técnico (leídas por el permiso)
    tech_allowed_actions = {'asignarme', 'estado_cliente', 'reagendar', 'cerrar'}

    filterset_fields = [
        'marca', 'tecnologia', 'encuesta', 'asignado_a', 'estado',
        'rut_cliente', 'id_vivienda', 'reagendado_fecha', 'reagendado_bloque',
    ]
    search_fields = ['direccion', 'rut_cliente', 'id_vivienda', 'id_qualtrics']

    # ---------------------------
    # Acciones de administración
    # ---------------------------
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
        u = request.user
        if getattr(u, 'rol', None) not in ('admin', 'auditor'):
            return Response({'detail': 'No autorizado.'}, status=403)

        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Falta archivo CSV en campo "file".'}, status=400)

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
            for idx, row in enumerate(reader, start=2):
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

    # ---------------------------
    # Acciones del técnico
    # ---------------------------
    @extend_schema(
        summary="Asignarme una dirección (técnico)",
        description="El técnico autenticado se asigna la dirección si está PENDIENTE.",
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=True, methods=['post'])
    def asignarme(self, request, pk=None):
        obj = self.get_object()
        if request.user.rol != 'tecnico':
            return Response({'detail': 'Solo técnicos pueden asignarse direcciones.'}, status=403)
        if obj.estado != EstadoAsignacion.PENDIENTE:
            return Response({'detail': 'La dirección no está disponible.'}, status=400)
        obj.asignado_a = request.user
        obj.estado = EstadoAsignacion.ASIGNADA
        obj.save(update_fields=['asignado_a', 'estado', 'updated_at'])
        return Response(self.get_serializer(obj).data)

    @extend_schema(
        summary="Prefill para el front (cabecera y choices)",
        description=(
            "Devuelve técnico asignado, datos de cliente, marca/tecnología y choices de 'Estado del Cliente'. "
            "Solo visible para el técnico asignado (o admin/auditor)."
        ),
        responses={
            200: {'type': 'object'},
            403: OpenApiResponse(description="No autorizado"),
        }
    )
    @action(detail=True, methods=['get'], url_path='prefill')
    def prefill(self, request, pk=None):
        obj = self.get_object()
        u = request.user

        # Técnico: solo si es el asignado; admin/auditor: libre
        if getattr(u, 'rol', None) == 'tecnico' and obj.asignado_a_id != u.id:
            return Response({'detail': 'No autorizado.'}, status=403)

        return Response({
            "tecnico_actual": (
                {
                    "id": obj.asignado_a.id,
                    "nombre": f"{obj.asignado_a.first_name} {obj.asignado_a.last_name}",
                    "email": obj.asignado_a.email,
                } if obj.asignado_a else None
            ),
            "cliente": {
                "rut": obj.rut_cliente,
                "id_vivienda": obj.id_vivienda,
                "direccion": obj.direccion,
            },
            "marca": obj.marca,
            "tecnologia": obj.tecnologia,
            "estado_cliente_choices": [
                {"value": "autoriza",      "label": "Autoriza a ingresar"},
                {"value": "sin_moradores", "label": "Sin Moradores"},
                {"value": "rechaza",       "label": "Rechaza"},
                {"value": "contingencia",  "label": "Contingencia externa"},
                {"value": "masivo",        "label": "Incidencia Masivo ClaroVTR"},
                {"value": "reagendo",      "label": "Reagendó"},
            ],
            "bloques": [
                {"value": "10-13", "label": "10:00 a 13:00"},
                {"value": "14-18", "label": "14:00 a 18:00"},
            ]
        })

    @extend_schema(
        summary="Estado del Cliente (acción única para técnico)",
        description=(
            "El técnico selecciona una de las 6 opciones:\n"
            "- autoriza → marca VISITADA y responde next='auditoria'.\n"
            "- reagendo → requiere fecha (YYYY-MM-DD) + bloque (10-13/14-18); deja REAGENDADA y next='gracias'.\n"
            "- sin_moradores / rechaza / contingencia / masivo → deja VISITADA y next='gracias'."
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'estado_cliente': {
                        'type': 'string',
                        'enum': ['autoriza', 'sin_moradores', 'rechaza', 'contingencia', 'masivo', 'reagendo']
                    },
                    'fecha':  {'type': 'string', 'format': 'date', 'example': '2025-09-26'},
                    'bloque': {'type': 'string', 'enum': ['10-13', '14-18']},
                },
                'required': ['estado_cliente']
            }
        },
        responses={
            200: {'type': 'object'},
            400: OpenApiResponse(description="Datos inválidos"),
            403: OpenApiResponse(description="No autorizado"),
        },
        examples=[
            OpenApiExample('Autoriza', value={'estado_cliente': 'autoriza'}),
            OpenApiExample('Reagendó', value={'estado_cliente': 'reagendo', 'fecha': '2025-09-26', 'bloque': '10-13'}),
            OpenApiExample('Rechaza',  value={'estado_cliente': 'rechaza'}),
        ]
    )
    @action(detail=True, methods=['post'], url_path='estado_cliente')
    def estado_cliente(self, request, pk=None):
        obj = self.get_object()
        u = request.user

        # Técnico: solo si es el asignado; admin/auditor: libre
        if getattr(u, 'rol', None) == 'tecnico' and obj.asignado_a_id != u.id:
            return Response({'detail': 'Solo el técnico asignado o admin/auditor puede operar.'}, status=403)

        estado = (request.data.get('estado_cliente') or '').strip().lower()

        if estado == 'autoriza':
            obj.estado = EstadoAsignacion.VISITADA
            obj.save(update_fields=['estado', 'updated_at'])
            return Response({'next': 'auditoria', 'asignacion': self.get_serializer(obj).data}, status=200)

        if estado == 'reagendo':
            fecha_str = (request.data.get('fecha') or '').strip()
            bloque = (request.data.get('bloque') or '').strip()
            if not fecha_str or not bloque:
                return Response({'detail': 'Debe enviar fecha (YYYY-MM-DD) y bloque (10-13/14-18).'}, status=400)
            fecha = parse_date(fecha_str)
            if not fecha:
                return Response({'detail': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
            if bloque not in ('10-13', '14-18'):
                return Response({'detail': 'Bloque inválido. Use 10-13 o 14-18.'}, status=400)

            obj.reagendado_fecha = fecha
            obj.reagendado_bloque = bloque
            obj.estado = EstadoAsignacion.REAGENDADA
            obj.save(update_fields=['reagendado_fecha', 'reagendado_bloque', 'estado', 'updated_at'])
            return Response({'next': 'gracias', 'asignacion': self.get_serializer(obj).data}, status=200)

        if estado in ('sin_moradores', 'rechaza', 'contingencia', 'masivo'):
            obj.estado = EstadoAsignacion.VISITADA
            obj.save(update_fields=['estado', 'updated_at'])
            return Response({'next': 'gracias', 'asignacion': self.get_serializer(obj).data}, status=200)

        return Response({'detail': 'estado_cliente inválido.'}, status=400)

    @extend_schema(
        summary="Reagendar visita (directo)",
        description="Reagenda con **fecha (YYYY-MM-DD)** y **bloque** (10-13 o 14-18).",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'fecha':  {'type': 'string', 'format': 'date', 'example': '2025-09-10'},
                    'bloque': {'type': 'string', 'enum': ['10-13', '14-18'], 'example': '10-13'},
                },
                'required': ['fecha', 'bloque'],
            }
        },
        responses=DireccionAsignadaSerializer,
        examples=[OpenApiExample('Reagendamiento', value={'fecha': '2025-09-10', 'bloque': '10-13'})],
    )
    @action(detail=True, methods=['post'], url_path='reagendar')
    def reagendar(self, request, pk=None):
        obj = self.get_object()
        u = request.user

        if getattr(u, 'rol', None) == 'tecnico' and obj.asignado_a_id != u.id:
            return Response({'detail': 'Solo el técnico asignado o auditor/admin puede reagendar.'}, status=403)

        fecha_str = (request.data.get('fecha') or '').strip()
        bloque = (request.data.get('bloque') or '').strip()

        if not fecha_str or not bloque:
            return Response({'detail': 'Debe enviar fecha (YYYY-MM-DD) y bloque (10-13/14-18).'}, status=400)

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
        summary="Cerrar visita sin auditoría",
        description="Para sin_moradores / rechaza / contingencia / masivo. Marca VISITADA.",
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
        obj = self.get_object()
        u = request.user

        if getattr(u, 'rol', None) == 'tecnico' and obj.asignado_a_id != u.id:
            return Response({'detail': 'No autorizado.'}, status=403)

        motivo = (request.data.get('motivo') or '').strip()
        if motivo not in ('sin_moradores', 'rechaza', 'contingencia', 'masivo'):
            return Response({'detail': 'motivo inválido.'}, status=400)

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
        if getattr(u, 'rol', None) != 'tecnico':
            return Response({'detail': 'Solo técnicos.'}, status=403)
        qs = self.get_queryset().filter(asignado_a=u)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)
