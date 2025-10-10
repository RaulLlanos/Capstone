from datetime import datetime
import csv
import io
import re
from typing import List, Dict, Any

from django.db.models import Case, When, Value, IntegerField, Q
from django.utils import timezone

from openpyxl import load_workbook
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema

from core.permissions import AdminFull_TechReadOnlyPlusActions
from usuarios.models import Usuario

from .models import DireccionAsignada, HistorialAsignacion
from .serializers import (
    DireccionAsignadaSerializer,
    HistorialAsignacionSerializer,
    CsvRowResult,
    CargaCSVSerializer,
    EstadoClienteActionSerializer,   # ⬅️ nuevo
)

# ➕ para la nueva acción
from auditoria.models import AuditoriaVisita
from .models import EstadoAsignacion, BloqueHorario

# ---------- Helpers para importar archivos ----------

_HEADER_ALIASES = {
    "rut_cliente": ["rut_cliente", "rut", "rut cliente"],
    # 🔧 priorizamos los nombres que usa Claro
    "id_vivienda": [
        "id_vivienda_cliente", "id_vivienda", "pcs_cliente",
        "customer_id", "customerid"
    ],
    "direccion": [
        "direccion_cliente", "direccion", "direccion del cliente",
        "dirección del cliente", "direccion_del_cliente",
        "direccion_destinatario", "direccion_cliente_del_destinatario"
    ],
    "comuna": [
        # 🔧 primero comuna_cliente (en tu archivo tiene datos; la columna "comuna" está vacía)
        "comuna_cliente", "comuna", "comuna del cliente", "comuna_del_cliente"
    ],
    "marca": ["marca", "brand"],
    "tecnologia": ["tecnologia", "customer_network_type"],
    "encuesta": ["encuesta", "encuesta de origen", "survey_type"],
    "id_qualtrics": ["id_qualtrics", "id_de_respuesta", "record_id"],
    "fecha": ["fecha", "fecha_programada", "fecha_registrada", "transactiondate"],
    "bloque": ["bloque", "bloque_horario", "bloque horario reagendamiento"],
    "asignado_email": ["asignado_email", "correo_tecnico", "tecnico_email", "email_tecnico"],
}

_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d")


def _norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    for a, b in {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n"}.items():
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s).replace(" ", "_")
    return s

def _s(val) -> str:
    """string seguro con strip(), manejando ints/None."""
    if val is None:
        return ""
    try:
        return str(val).strip()
    except Exception:
        return ""

def _build_header_map(raw_headers: List[str]) -> Dict[str, str]:
    norm_headers = { _norm(h): h for h in raw_headers }
    mapping = {}
    for canon, aliases in _HEADER_ALIASES.items():
        for alias in aliases:
            k = _norm(alias)
            if k in norm_headers:
                mapping[canon] = norm_headers[k]
                break
    return mapping

def _parse_date(val):
    if not val:
        return None
    # Si viene ya como datetime/date desde openpyxl
    if hasattr(val, "year"):
        try:
            return val.date() if hasattr(val, "date") else val
        except Exception:
            pass
    val = _s(val)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt).date()
        except Exception:
            pass
    return None

def _normalize_bloque(val: str) -> str | None:
    v = _s(val).lower()
    if not v:
        return None
    if "10" in v and "13" in v:
        return "10-13"
    if "14" in v and "18" in v:
        return "14-18"
    if v in {"10-13", "14-18"}:
        return v
    return None

def _header_score(names_norm: List[str]) -> int:
    """Heurística para detectar la fila de encabezados en XLSX."""
    score = 0
    have = set(names_norm)
    def any_alias(key):
        return any(_norm(a) in have for a in _HEADER_ALIASES[key])
    for key in ("direccion", "comuna", "id_vivienda", "rut_cliente", "fecha"):
        if any_alias(key):
            score += 1
    return score

def _rows_from_csv(f) -> List[Dict[str, Any]]:
    data = f.read().decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(data))
    headers = list(reader.fieldnames or [])
    header_map = _build_header_map(headers)
    return [(header_map, r) for r in reader]

def _rows_from_xlsx(f) -> List[Dict[str, Any]]:
    wb = load_workbook(filename=io.BytesIO(f.read()), data_only=True)
    ws = wb.worksheets[0]

    all_rows = list(ws.iter_rows(values_only=True))
    if not all_rows:
        return []

    # intenta detectar la fila de headers (primeras 10 filas)
    header_idx = 0
    for i in range(min(10, len(all_rows))):
        names = [ _s(x) for x in (all_rows[i] or []) ]
        if _header_score([_norm(n) for n in names]) >= 2:
            header_idx = i
            break

    headers = [ _s(x) for x in (all_rows[header_idx] or []) ]
    header_map = _build_header_map(headers)

    rows = []
    for raw in all_rows[header_idx+1:]:
        if not any(raw):  # fila completamente vacía
            continue
        r = { headers[i]: (raw[i] if i < len(raw) else None) for i in range(len(headers)) }
        rows.append((header_map, r))
    return rows

def _canon_get(row: Dict[str, Any], header_map: Dict[str, str], key: str) -> Any:
    src = header_map.get(key)
    return row.get(src) if src else None

# ---------------------------------------------------


class DireccionAsignadaViewSet(viewsets.ModelViewSet):
    """
    - Administrador: CRUD total + carga CSV/XLSX + reasignar/desasignar
    - Técnico: lectura + acciones (asignarme, estado_cliente, reagendar, cerrar)
    """
    queryset = DireccionAsignada.objects.all().order_by("-created_at")
    serializer_class = DireccionAsignadaSerializer
    permission_classes = [IsAuthenticated, AdminFull_TechReadOnlyPlusActions]

    filterset_fields = ["estado", "comuna", "zona", "marca", "tecnologia", "encuesta", "asignado_a"]
    search_fields = ["direccion", "comuna", "rut_cliente", "id_vivienda"]
    ordering_fields = ["fecha", "created_at"]

    # 👇 Para que el Browsable API muestre el formulario correcto en la acción
    def get_serializer_class(self):
        if getattr(self, "action", None) == "cargar_csv":
            return CargaCSVSerializer
        if getattr(self, "action", None) == "estado_cliente":
            return EstadoClienteActionSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        u = self.request.user
        qs = DireccionAsignada.objects.all()

        if self.request.query_params.get("mine") and getattr(u, "rol", None) == "tecnico":
            qs = qs.filter(asignado_a_id=u.id)

        order = self.request.query_params.get("order", "").lower()
        if order == "prioridad":
            prioridad = Case(
                When(reagendado_fecha__isnull=False, then=Value(1)),
                When(asignado_a__isnull=False, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
            qs = qs.annotate(prioridad=prioridad).order_by("prioridad", "fecha", "id")
        else:
            qs = qs.order_by("fecha", "id")

        fgte = self.request.query_params.get("fecha__gte")
        flte = self.request.query_params.get("fecha__lte")
        if fgte: qs = qs.filter(fecha__gte=fgte)
        if flte: qs = qs.filter(fecha__lte=flte)

        return qs

    @action(detail=False, methods=["get"], url_path="historial")
    def historial(self, request):
        u = request.user
        tecnico_id = request.query_params.get("tecnico_id")
        qs = HistorialAsignacion.objects.select_related("asignacion", "usuario").all()

        if getattr(u, "rol", None) == "tecnico":
            qs = qs.filter(Q(usuario_id=u.id) | Q(asignacion__asignado_a_id=u.id))
        else:
            if tecnico_id:
                qs = qs.filter(Q(usuario_id=tecnico_id) | Q(asignacion__asignado_a_id=tecnico_id))

        qs = qs.order_by("-created_at", "-id")
        page = self.paginate_queryset(qs)
        s = HistorialAsignacionSerializer(page or qs, many=True)
        return self.get_paginated_response(s.data) if page is not None else Response(s.data)

    # === CARGA CSV/XLSX semanal ===
    @extend_schema(request=CargaCSVSerializer)  # para que en /docs aparezca el input "file"
    @action(
        detail=False,
        methods=["post"],
        url_path="cargar_csv",
        parser_classes=[MultiPartParser, FormParser],
        serializer_class=CargaCSVSerializer,  # para que el Browsable API muestre el campo file
    )
    def cargar_csv(self, request):
        """
        Acepta:
        - CSV (.csv)
        - Excel (.xlsx) primera hoja

        Mapea encabezados del archivo de Claro a nuestros nombres canónicos,
        detectando automáticamente la fila real de encabezados en XLSX.
        """
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "Sube un archivo en el campo 'file'."}, status=400)

        name = (_s(f.name)).lower()
        try:
            rows = _rows_from_xlsx(f) if name.endswith(".xlsx") else _rows_from_csv(f)
        except Exception as e:
            return Response({"detail": f"No se pudo leer el archivo: {e}"}, status=400)

        results = []
        today = timezone.localdate()

        for idx, (header_map, row) in enumerate(rows, start=2):
            errors = []
            created = False
            updated = False

            rut_cliente   = _s(_canon_get(row, header_map, "rut_cliente"))
            id_vivienda   = _s(_canon_get(row, header_map, "id_vivienda"))
            direccion     = _s(_canon_get(row, header_map, "direccion"))
            comuna        = _s(_canon_get(row, header_map, "comuna"))

            marca      = (_s(_canon_get(row, header_map, "marca")) or "CLARO").upper()
            tecnologia = (_s(_canon_get(row, header_map, "tecnologia")) or "HFC").upper()
            encuesta   = (_s(_canon_get(row, header_map, "encuesta")) or "post_visita").lower()
            id_qual    = _s(_canon_get(row, header_map, "id_qualtrics"))

            fecha_val  = _parse_date(_canon_get(row, header_map, "fecha"))
            bloque     = _normalize_bloque(_canon_get(row, header_map, "bloque"))
            asignado_email = _s(_canon_get(row, header_map, "asignado_email"))

            # Fechas pasadas → las ignoramos (queda sin fecha)
            if fecha_val and fecha_val < today:
                fecha_val = None

            if not direccion or not comuna:
                errors.append("Faltan campos obligatorios: direccion/comuna.")

            asignado = None
            if asignado_email:
                asignado = Usuario.objects.filter(email__iexact=asignado_email, rol="tecnico").first()
                if not asignado:
                    errors.append("asignado_email no existe o no es técnico.")

            if errors:
                results.append({"rownum": idx, "created": False, "updated": False, "errors": errors})
                continue

            defaults = {
                "rut_cliente": rut_cliente,
                "direccion": direccion,
                "comuna": comuna,
                "marca": marca or "CLARO",
                "tecnologia": tecnologia or "HFC",
                "encuesta": encuesta or "post_visita",
                "id_qualtrics": id_qual,
            }
            if fecha_val:
                defaults["fecha"] = fecha_val

            # upsert por id_vivienda si viene, si no por (direccion, comuna)
            if id_vivienda:
                obj, was_created = DireccionAsignada.objects.get_or_create(
                    id_vivienda=id_vivienda,
                    defaults={**defaults, "estado": "PENDIENTE"},
                )
            else:
                obj, was_created = DireccionAsignada.objects.get_or_create(
                    direccion=direccion,
                    comuna=comuna,
                    defaults={**defaults, "estado": "PENDIENTE"},
                )

            # seteo/actualizo
            for k, v in defaults.items():
                setattr(obj, k, v)

            if bloque:
                obj.reagendado_bloque = None  # (opcional)

            # estado / técnico
            if asignado:
                obj.asignado_a = asignado
                if not obj.fecha and fecha_val:
                    obj.fecha = fecha_val
                obj.estado = "ASIGNADA"
            else:
                obj.asignado_a = None
                obj.estado = "PENDIENTE"

            obj.save()

            if was_created:
                HistorialAsignacion.objects.create(
                    asignacion=obj,
                    accion="creada",
                    detalles=f"Creada por carga XLS/CSV. {'Asignada a ' + asignado.email if asignado else 'Sin técnico'}",
                    usuario=request.user,
                )
                created = True
            else:
                HistorialAsignacion.objects.create(
                    asignacion=obj,
                    accion="editada",
                    detalles="Actualizada por carga XLS/CSV.",
                    usuario=request.user,
                )
                updated = True

            results.append({"rownum": idx, "created": created, "updated": updated})

        return Response({
            "ok": True,
            "rows": results,
            "summary": {
                "created": sum(1 for r in results if r["created"]),
                "updated": sum(1 for r in results if r["updated"]),
                "errors":  sum(1 for r in results if r.get("errors")),
            }
        })

    # ✅ NUEVA ACCIÓN: técnico marca el estado del cliente en una visita asignada
    @extend_schema(
        request=EstadoClienteActionSerializer,
        responses={200: DireccionAsignadaSerializer}
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="estado_cliente",
        serializer_class=EstadoClienteActionSerializer,  # fuerza el formulario correcto en Browsable API
    )
    def estado_cliente(self, request, pk=None):
        user = request.user
        if getattr(user, "rol", None) != "tecnico":
            return Response({"detail": "Solo técnicos pueden usar esta acción."}, status=status.HTTP_403_FORBIDDEN)

        asignacion = self.get_object()
        if asignacion.asignado_a_id != user.id:
            return Response({"detail": "Esta dirección no está asignada a tu usuario."}, status=status.HTTP_403_FORBIDDEN)

        # Valida payload con serializer (aparece como formulario en Browsable API)
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        estado = data["estado_cliente"]
        reagendado_fecha = data.get("reagendado_fecha")
        reagendado_bloque = data.get("reagendado_bloque")
        ont_modem_ok = data.get("ont_modem_ok", None)
        servicios = data.get("servicios") or []
        categorias = data.get("categorias") or {}
        descripcion_problema = data.get("descripcion_problema") or ""
        fotos = data.get("fotos") or []

        # Validación específica para reagendo
        if estado == "reagendo":
            if not reagendado_fecha or not reagendado_bloque:
                return Response({"detail": "Debe indicar reagendado_fecha y reagendado_bloque."}, status=400)
            if reagendado_fecha < timezone.localdate():
                return Response({"detail": "La fecha reagendada no puede ser pasada."}, status=400)

        # Crear auditoría como traza formal
        audit = AuditoriaVisita.objects.create(
            asignacion=asignacion,
            tecnico=user,
            estado_cliente=estado,
            reagendado_fecha=reagendado_fecha,
            reagendado_bloque=reagendado_bloque,
            ont_modem_ok=ont_modem_ok,
            servicios=servicios,
            categorias=categorias,
            descripcion_problema=descripcion_problema,
            fotos=fotos,
        )

        # Efectos sobre la asignación + historial (mapeo a estado de asignación)
        if estado == "reagendo":
            asignacion.reagendado_fecha = audit.reagendado_fecha
            asignacion.reagendado_bloque = audit.reagendado_bloque
            asignacion.estado = EstadoAsignacion.REAGENDADA
            asignacion.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado", "updated_at"])
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion=HistorialAsignacion.Accion.REAGENDADA,
                detalles=f"Reagendada por técnico a {audit.reagendado_fecha} {audit.reagendado_bloque}",
                usuario=user,
            )
        elif estado == "autoriza":
            asignacion.estado = EstadoAsignacion.VISITADA
            asignacion.save(update_fields=["estado", "updated_at"])
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion=HistorialAsignacion.Accion.AUDITORIA_CREADA,
                detalles="Auditoría con estado 'autoriza' (asignación VISITADA).",
                usuario=user,
            )
        else:
            # sin_moradores / rechaza / contingencia / masivo → CANCELADA
            asignacion.estado = EstadoAsignacion.CANCELADA
            asignacion.save(update_fields=["estado", "updated_at"])
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion=HistorialAsignacion.Accion.ESTADO_CLIENTE,
                detalles=f"Estado cliente = {estado} (asignación CANCELADA).",
                usuario=user,
            )

        # Respuesta: asignación (para refrescar la tarjeta en el front)
        return Response(DireccionAsignadaSerializer(asignacion).data, status=200)

    @action(detail=True, methods=["patch"], url_path="desasignar")
    def desasignar(self, request, pk=None):
        obj = self.get_object()
        if getattr(request.user, "rol", None) != "administrador":
            return Response({"detail": "Solo administrador puede desasignar."}, status=403)
        obj.asignado_a = None
        obj.estado = "PENDIENTE"
        obj.save()
        HistorialAsignacion.objects.create(
            asignacion=obj,
            accion="asignacion_eliminada",
            detalles="Desasignada por administrador.",
            usuario=request.user,
        )
        return Response(self.get_serializer(obj).data)
