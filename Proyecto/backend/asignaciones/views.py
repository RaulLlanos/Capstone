from django.db.models import Q
from django.utils.dateparse import parse_date
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

import csv, io
from django.db import transaction

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiTypes, OpenApiExample, OpenApiResponse
)

from core.permissions import AdminAuditorFull_TechReadOnlyPlusActions
from .models import DireccionAsignada, EstadoAsignacion, HistorialAsignacion
from .serializers import DireccionAsignadaSerializer, DireccionAsignadaListaSerializer
from .comunas import zona_para_comuna, COMUNAS_SANTIAGO
from usuarios.models import Usuario

@extend_schema_view(
    list=extend_schema(
        summary="Listar direcciones",
        description="Lista paginada y filtrable de direcciones.",
        parameters=[
            OpenApiParameter("marca", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("tecnologia", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("encuesta", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("asignado_a", OpenApiTypes.INT, OpenApiParameter.QUERY),
            OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("rut_cliente", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("id_vivienda", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("comuna", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("zona", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("fecha", OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter("reagendado_fecha", OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter("reagendado_bloque", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description="Busca en dirección, comuna, RUT, id_vivienda, id_qualtrics"),
        ],
        responses=DireccionAsignadaListaSerializer,
    ),
    retrieve=extend_schema(summary="Detalle de dirección", responses=DireccionAsignadaSerializer),
    create=extend_schema(summary="Crear dirección (solo auditor/admin)", responses=DireccionAsignadaSerializer),
)
class DireccionAsignadaViewSet(viewsets.ModelViewSet):
    """
    - Auditor/Admin: CRUD total + carga CSV
    - Técnico: lectura + acciones: asignarme, prefill, estado_cliente, reagendar, cerrar
    """
    queryset = DireccionAsignada.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnlyPlusActions]
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    tech_allowed_actions = {"asignarme", "estado_cliente", "reagendar", "cerrar"}

    filterset_fields = [
        "marca", "tecnologia", "encuesta", "asignado_a", "estado",
        "rut_cliente", "id_vivienda", "comuna", "zona", "fecha",
        "reagendado_fecha", "reagendado_bloque",
    ]
    search_fields = ["direccion", "comuna", "rut_cliente", "id_vivienda", "id_qualtrics"]

    def get_serializer_class(self):
        if self.action in ("list", "disponibles", "mias", "tablero"):
            return DireccionAsignadaListaSerializer
        return DireccionAsignadaSerializer

    # ---------------------------
    # Carga masiva CSV (auditor)
    # ---------------------------
    @extend_schema(
        summary="Carga masiva (CSV) (auditor/admin)",
        description=(
            "Sube un CSV UTF-8 con encabezados: "
            "`fecha, tecnologia, marca, rut_cliente, id_vivienda, direccion, comuna, encuesta, id_qualtrics`. "
            "La `zona` se calcula automáticamente según la comuna."
        ),
        examples=[
            OpenApiExample(
                "CSV esperado",
                description="Contenido ejemplo (2 filas)",
                value=(
                    "fecha,tecnologia,marca,rut_cliente,id_vivienda,direccion,comuna,encuesta,id_qualtrics\n"
                    "2025-10-05,FTTH,CLARO,12.345.678-9,HOME-001,\"Av. Siempre Viva 123\",Ñuñoa,instalacion,QX-001\n"
                    "2025-10-06,HFC,VTR,9.876.543-2,HOME-002,\"Los Olmos 456\",Maipú,post_visita,QX-002\n"
                ),
            )
        ],
        responses={201: {"type": "object", "properties": {"created": {"type": "integer"}}}},
    )
    @action(detail=False, methods=["post"])
    def upload_csv(self, request):
        u = request.user
        if getattr(u, "rol", None) not in ("admin", "auditor") and not getattr(u, "is_superuser", False):
            return Response({"detail": "No autorizado."}, status=403)

        file = request.FILES.get("file")
        if not file:
            return Response({"detail": 'Falta archivo CSV en campo "file".'}, status=400)

        try:
            decoded = file.read().decode("utf-8")
        except UnicodeDecodeError:
            return Response({"detail": "El CSV debe estar en UTF-8."}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        required = {"fecha", "tecnologia", "marca", "rut_cliente", "id_vivienda", "direccion", "comuna", "encuesta"}
        headers = set([h.strip() for h in (reader.fieldnames or [])])
        if not required.issubset(headers):
            return Response({"detail": f"Encabezados requeridos: {sorted(required)}"}, status=400)

        created = 0
        today = timezone.localdate()

        with transaction.atomic():
            for idx, row in enumerate(reader, start=2):
                fecha_str = (row.get("fecha") or "").strip()
                fecha_val = parse_date(fecha_str) if fecha_str else None
                if fecha_str and not fecha_val:
                    return Response({"detail": f'Fila {idx}: fecha inválida "{fecha_str}" (use YYYY-MM-DD).'}, status=400)
                if fecha_val and fecha_val < today:
                    return Response({"detail": f"Fila {idx}: la fecha no puede ser en el pasado."}, status=400)

                comuna = (row.get("comuna") or "").strip()
                if not comuna:
                    return Response({"detail": f"Fila {idx}: falta comuna."}, status=400)
                try:
                    zona = zona_para_comuna(comuna)
                except ValueError:
                    return Response({"detail": f"Fila {idx}: comuna no válida para Santiago."}, status=400)

                DireccionAsignada.objects.create(
                    fecha=fecha_val,
                    tecnologia=(row["tecnologia"] or "").strip().upper(),
                    marca=(row["marca"] or "").strip().upper(),
                    rut_cliente=(row["rut_cliente"] or "").strip(),
                    id_vivienda=(row["id_vivienda"] or "").strip(),
                    direccion=(row["direccion"] or "").strip(),
                    comuna=comuna,
                    zona=zona,  # calculada
                    encuesta=(row["encuesta"] or "").strip(),
                    id_qualtrics=(row.get("id_qualtrics") or "").strip(),
                )
                created += 1

        return Response({"created": created}, status=201)

    # ---------------------------
    # Acciones del técnico/auditor
    # ---------------------------

    @extend_schema(
        summary="Ver si me puedo asignar (preview) y datos de la dirección",
        responses={200: {"type": "object"}},
    )
    @action(detail=True, methods=["get", "post"])
    def asignarme(self, request, pk=None):
        obj = self.get_object()

        if request.method == "GET":
            can = (obj.asignado_a_id is None) and (obj.estado == EstadoAsignacion.PENDIENTE)
            reason = None
            if obj.asignado_a_id:
                reason = f"Ya asignada a {obj.asignado_a.email}"
            elif obj.estado != EstadoAsignacion.PENDIENTE:
                reason = f"Estado actual={obj.estado} (requiere PENDIENTE)"
            return Response({
                "can_asignarme": can,
                "reason": reason,
                "asignacion": DireccionAsignadaListaSerializer(obj, context={"request": request}).data,
            })

        if request.user.rol != "tecnico":
            return Response({"detail": "Solo técnicos pueden asignarse direcciones."}, status=403)
        if obj.asignado_a_id:
            return Response({"detail": f"No disponible: ya asignada a {obj.asignado_a.email}."}, status=400)
        if obj.estado != EstadoAsignacion.PENDIENTE:
            return Response({"detail": f"No disponible: estado actual={obj.estado} (requiere PENDIENTE)."}, status=400)

        obj.asignado_a = request.user
        obj.estado = EstadoAsignacion.ASIGNADA
        obj.save(update_fields=["asignado_a", "estado", "updated_at"])

        HistorialAsignacion.objects.create(
            asignacion=obj,
            accion=HistorialAsignacion.Accion.ASIGNADA_TECNICO,
            detalles=f"Autoasignada por técnico {request.user.email}",
            usuario=request.user,
        )
        return Response(DireccionAsignadaSerializer(obj, context={"request": request}).data)

    @extend_schema(
        summary="Asignar a un técnico (auditor/admin)",
        request={'application/json': {
            'type': 'object',
            'properties': {'tecnico_id': {'type': 'integer'}},
            'required': ['tecnico_id'],
        }},
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=True, methods=["patch"], url_path="asignar_a")
    def asignar_a(self, request, pk=None):
        obj = self.get_object()
        u = request.user
        if getattr(u, "rol", None) != "auditor" and not getattr(u, "is_superuser", False):
            return Response({"detail": "Solo auditor/admin."}, status=403)

        try:
            tecnico_id = int(request.data.get("tecnico_id"))
        except (TypeError, ValueError):
            return Response({"detail": "tecnico_id inválido."}, status=400)

        try:
            tech = Usuario.objects.get(id=tecnico_id, rol="tecnico", is_active=True)
        except Usuario.DoesNotExist:
            return Response({"detail": "Técnico no encontrado o inactivo."}, status=404)

        prev = obj.asignado_a
        obj.asignado_a = tech
        obj.estado = EstadoAsignacion.ASIGNADA
        obj.save(update_fields=["asignado_a", "estado", "updated_at"])

        HistorialAsignacion.objects.create(
            asignacion=obj,
            accion=HistorialAsignacion.Accion.ASIGNADA_TECNICO,
            detalles=f"Asignada por auditor a {tech.email} (antes: {prev.email if prev else 'sin técnico'})",
            usuario=u,
        )
        return Response(DireccionAsignadaSerializer(obj, context={"request": request}).data)

    @extend_schema(
        summary="Desasignar (auditor/admin) y dejar PENDIENTE",
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=True, methods=["patch"], url_path="desasignar")
    def desasignar(self, request, pk=None):
        obj = self.get_object()
        u = request.user
        if getattr(u, "rol", None) != "auditor" and not getattr(u, "is_superuser", False):
            return Response({"detail": "Solo auditor/admin."}, status=403)

        if obj.estado == EstadoAsignacion.VISITADA:
            return Response({"detail": "No se puede desasignar una visita completada."}, status=400)

        prev = obj.asignado_a
        obj.asignado_a = None
        obj.estado = EstadoAsignacion.PENDIENTE
        obj.save(update_fields=["asignado_a", "estado", "updated_at"])

        HistorialAsignacion.objects.create(
            asignacion=obj,
            accion=HistorialAsignacion.Accion.DESASIGNADA,
            detalles=f"Desasignada (antes: {prev.email if prev else 'sin técnico'})",
            usuario=u,
        )
        return Response(DireccionAsignadaSerializer(obj, context={"request": request}).data)

    @extend_schema(
        summary="Prefill para el front (cabecera y choices)",
        responses={200: {"type": "object"}, 403: OpenApiResponse(description="No autorizado")},
    )
    @action(detail=True, methods=["get"], url_path="prefill")
    def prefill(self, request, pk=None):
        obj = self.get_object()
        u = request.user
        if getattr(u, "rol", None) == "tecnico" and obj.asignado_a_id != u.id:
            return Response({"detail": "No autorizado."}, status=403)

        return Response({
            "tecnico_actual": (
                {"id": obj.asignado_a.id,
                 "nombre": f"{obj.asignado_a.first_name} {obj.asignado_a.last_name}".strip(),
                 "email": obj.asignado_a.email}
                if obj.asignado_a else None
            ),
            "cliente": {
                "rut": obj.rut_cliente,
                "id_vivienda": obj.id_vivienda,
                "direccion": obj.direccion,
                "comuna": obj.comuna,
                "zona": obj.zona,
            },
            "marca": obj.marca,
            "tecnologia": obj.tecnologia,
            "estado_cliente_choices": [
                {"value": "autoriza", "label": "Autoriza a ingresar"},
                {"value": "sin_moradores", "label": "Sin Moradores"},
                {"value": "rechaza", "label": "Rechaza"},
                {"value": "contingencia", "label": "Contingencia externa"},
                {"value": "masivo", "label": "Incidencia Masivo ClaroVTR"},
                {"value": "reagendo", "label": "Reagendó"},
            ],
            "bloques": [
                {"value": "10-13", "label": "10:00 a 13:00"},
                {"value": "14-18", "label": "14:00 a 18:00"},
            ],
        })

    @extend_schema(
        summary="Estado del Cliente (acción única para técnico)",
        request={'application/json': {
            'type': 'object',
            'properties': {
                'estado_cliente': {'type': 'string', 'enum': ['autoriza','sin_moradores','rechaza','contingencia','masivo','reagendo']},
                'fecha':  {'type': 'string', 'format': 'date'},
                'bloque': {'type': 'string', 'enum': ['10-13','14-18']},
            },
            'required': ['estado_cliente'],
        }},
        responses={200: {"type": "object"}, 400: OpenApiResponse(description="Datos inválidos"), 403: OpenApiResponse(description="No autorizado")},
    )
    @action(detail=True, methods=["post"], url_path="estado_cliente")
    def estado_cliente(self, request, pk=None):
        obj = self.get_object()
        u = request.user
        if getattr(u, "rol", None) == "tecnico" and obj.asignado_a_id != u.id:
            return Response({"detail": "Solo el técnico asignado o admin/auditor puede operar."}, status=403)

        estado = (request.data.get("estado_cliente") or "").strip().lower()

        if estado == "autoriza":
            obj.estado = EstadoAsignacion.VISITADA
            obj.save(update_fields=["estado", "updated_at"])
            return Response({"next": "auditoria", "asignacion": DireccionAsignadaSerializer(obj).data})

        if estado == "reagendo":
            fecha_str = (request.data.get("fecha") or "").strip()
            bloque = (request.data.get("bloque") or "").strip()
            if not fecha_str or not bloque:
                return Response({"detail": "Debe enviar fecha (YYYY-MM-DD) y bloque (10-13/14-18)."}, status=400)
            fecha = parse_date(fecha_str)
            if not fecha:
                return Response({"detail": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)
            if fecha < timezone.localdate():
                return Response({"detail": "La fecha no puede ser en el pasado."}, status=400)
            if bloque not in ("10-13", "14-18"):
                return Response({"detail": "Bloque inválido. Use 10-13 o 14-18."}, status=400)

            obj.reagendado_fecha = fecha
            obj.reagendado_bloque = bloque
            obj.estado = EstadoAsignacion.REAGENDADA
            obj.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado", "updated_at"])
            return Response({"next": "gracias", "asignacion": DireccionAsignadaSerializer(obj).data})

        if estado in ("sin_moradores", "rechaza", "contingencia", "masivo"):
            obj.estado = EstadoAsignacion.VISITADA
            obj.save(update_fields=["estado", "updated_at"])
            return Response({"next": "gracias", "asignacion": DireccionAsignadaSerializer(obj).data})

        return Response({"detail": "estado_cliente inválido."}, status=400)

    @extend_schema(
        summary="Reagendar visita (directo)",
        request={'application/json': {
            'type': 'object',
            'properties': {'fecha': {'type': 'string', 'format': 'date'}, 'bloque': {'type': 'string', 'enum': ['10-13','14-18']}},
            'required': ['fecha','bloque'],
        }},
        responses=DireccionAsignadaSerializer,
    )
    @action(detail=True, methods=["post"], url_path="reagendar")
    def reagendar(self, request, pk=None):
        obj = self.get_object()
        u = request.user
        if getattr(u, "rol", None) == "tecnico" and obj.asignado_a_id != u.id:
            return Response({"detail": "Solo el técnico asignado o auditor/admin puede reagendar."}, status=403)

        fecha_str = (request.data.get("fecha") or "").strip()
        bloque = (request.data.get("bloque") or "").strip()
        if not fecha_str or not bloque:
            return Response({"detail": "Debe enviar fecha (YYYY-MM-DD) y bloque (10-13/14-18)."}, status=400)

        fecha = parse_date(fecha_str)
        if not fecha:
            return Response({"detail": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)
        if fecha < timezone.localdate():
            return Response({"detail": "La fecha no puede ser en el pasado."}, status=400)
        if bloque not in ("10-13", "14-18"):
            return Response({"detail": "Bloque inválido. Use 10-13 o 14-18."}, status=400)

        obj.reagendado_fecha = fecha
        obj.reagendado_bloque = bloque
        obj.estado = EstadoAsignacion.REAGENDADA
        obj.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado", "updated_at"])

        return Response(DireccionAsignadaSerializer(obj).data)

    @extend_schema(summary="Mis direcciones (técnico)", responses=DireccionAsignadaListaSerializer)
    @action(detail=False, methods=["get"], url_path="mias")
    def mias(self, request):
        u = request.user
        if getattr(u, "rol", None) != "tecnico":
            return Response({"detail": "Solo técnicos."}, status=403)
        qs = self.get_queryset().filter(asignado_a=u).order_by("fecha", "comuna", "direccion")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    @extend_schema(
        summary="Direcciones disponibles para asignarme (técnico)",
        parameters=[
            OpenApiParameter("zona", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("comuna", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("marca", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("tecnologia", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("desde", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="fecha mínima"),
            OpenApiParameter("hasta", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="fecha máxima"),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        responses=DireccionAsignadaListaSerializer,
    )
    @action(detail=False, methods=["get"], url_path="disponibles")
    def disponibles(self, request):
        u = request.user
        if getattr(u, "rol", None) != "tecnico":
            return Response({"detail": "Solo técnicos."}, status=403)

        qs = self.get_queryset().filter(asignado_a__isnull=True, estado=EstadoAsignacion.PENDIENTE)

        zona   = (request.query_params.get("zona") or "").strip().upper()
        comuna = (request.query_params.get("comuna") or "").strip()
        marca  = (request.query_params.get("marca") or "").strip().upper()
        tec    = (request.query_params.get("tecnologia") or "").strip().upper()
        s      = (request.query_params.get("search") or "").strip()

        if zona:   qs = qs.filter(zona=zona)
        if comuna: qs = qs.filter(comuna__icontains=comuna)
        if marca:  qs = qs.filter(marca=marca)
        if tec:    qs = qs.filter(tecnologia=tec)

        desde = parse_date(request.query_params.get("desde") or "")
        hasta = parse_date(request.query_params.get("hasta") or "")
        if desde: qs = qs.filter(fecha__gte=desde)
        if hasta: qs = qs.filter(fecha__lte=hasta)

        if s:
            qs = qs.filter(
                Q(direccion__icontains=s) |
                Q(comuna__icontains=s) |
                Q(rut_cliente__icontains=s) |
                Q(id_vivienda__icontains=s)
            )

        qs = qs.order_by("fecha", "comuna", "direccion")

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    @extend_schema(
        summary="Tablero del técnico: mías + disponibles",
        parameters=[
            OpenApiParameter("zona", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("comuna", OpenApiTypes.STR, OpenApiParameter.QUERY),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY),
        ],
        responses={200: {"type": "object"}},
    )
    @action(detail=False, methods=["get"], url_path="tablero")
    def tablero(self, request):
        u = request.user
        if getattr(u, "rol", None) != "tecnico":
            return Response({"detail": "Solo técnicos."}, status=403)

        zona   = (request.query_params.get("zona") or "").strip().upper()
        comuna = (request.query_params.get("comuna") or "").strip()
        s      = (request.query_params.get("search") or "").strip()

        mias = self.get_queryset().filter(asignado_a=u).order_by("fecha", "comuna", "direccion")
        if zona:   mias = mias.filter(zona=zona)
        if comuna: mias = mias.filter(comuna__icontains=comuna)
        if s:
            mias = mias.filter(Q(direccion__icontains=s) | Q(comuna__icontains=s))

        disp = self.get_queryset().filter(asignado_a__isnull=True, estado=EstadoAsignacion.PENDIENTE).order_by("fecha", "comuna", "direccion")
        if zona:   disp = disp.filter(zona=zona)
        if comuna: disp = disp.filter(comuna__icontains=comuna)
        if s:
            disp = disp.filter(Q(direccion__icontains=s) | Q(comuna__icontains=s))

        return Response({
            "mias": DireccionAsignadaListaSerializer(mias[:100], many=True, context={"request": request}).data,
            "disponibles": DireccionAsignadaListaSerializer(disp[:100], many=True, context={"request": request}).data,
        })

AsignacionViewSet = DireccionAsignadaViewSet
