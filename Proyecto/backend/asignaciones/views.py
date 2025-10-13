# asignaciones/views.py
from datetime import datetime
import csv
import io
import re
from typing import List, Dict, Any

from django.db import transaction
from django.db.models import Case, When, Value, IntegerField, Q, Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone

from openpyxl import load_workbook, Workbook
from rest_framework import viewsets
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
)

# === Notificaciones (registro + envío real por email) ===
from core.models import Notificacion
from core.notify import enviar_notificacion_real

# ---------- Helpers para importar archivos ----------

_HEADER_ALIASES = {
    "rut_cliente": ["rut_cliente", "rut", "rut cliente"],
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
        if not any(raw):
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
    - Administrador: CRUD total + carga CSV/XLSX + reasignar/desasignar.
    - Técnico: lectura + acción POST /estado_cliente/.
    """
    queryset = DireccionAsignada.objects.all().order_by("-created_at")
    serializer_class = DireccionAsignadaSerializer
    permission_classes = [IsAuthenticated, AdminFull_TechReadOnlyPlusActions]

    filterset_fields = ["estado", "comuna", "zona", "marca", "tecnologia", "encuesta", "asignado_a"]
    search_fields = ["direccion", "comuna", "rut_cliente", "id_vivienda"]
    ordering_fields = ["fecha", "created_at"]

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

    # ---------- helper: mismo filtro de historial para listar/exportar ----------
    def _historial_filtered_qs(self, request):
        u = request.user
        tecnico_id = request.query_params.get("tecnico_id")
        qs = HistorialAsignacion.objects.select_related("asignacion", "usuario").all()

        if getattr(u, "rol", None) == "tecnico":
            qs = qs.filter(Q(usuario_id=u.id) | Q(asignacion__asignado_a_id=u.id))
        elif tecnico_id:
            qs = qs.filter(Q(usuario_id=tecnico_id) | Q(asignacion__asignado_a_id=tecnico_id))

        # Filtros de campos de asignación
        p = request.query_params
        if p.get("estado"): qs = qs.filter(asignacion__estado=p["estado"])
        if p.get("marca"): qs = qs.filter(asignacion__marca=p["marca"])
        if p.get("tecnologia"): qs = qs.filter(asignacion__tecnologia=p["tecnologia"])
        if p.get("comuna"): qs = qs.filter(asignacion__comuna=p["comuna"])
        if p.get("zona"): qs = qs.filter(asignacion__zona=p["zona"])
        if p.get("encuesta"): qs = qs.filter(asignacion__encuesta=p["encuesta"])

        # Rango por fecha de asignación (alias desde/hasta y HOY)
        desde = p.get("fecha_after") or p.get("desde")
        hasta = p.get("fecha_before") or p.get("hasta")
        hoy = timezone.localdate().isoformat()
        if desde and str(desde).upper() == "HOY": desde = hoy
        if hasta and str(hasta).upper() == "HOY": hasta = hoy
        if desde: qs = qs.filter(asignacion__fecha__gte=desde)
        if hasta: qs = qs.filter(asignacion__fecha__lte=hasta)

        return qs

    # ---------- HISTORIAL (lista) ----------
    @action(detail=False, methods=["get"], url_path="historial")
    def historial(self, request):
        qs = self._historial_filtered_qs(request).order_by("-created_at", "-id")
        page = self.paginate_queryset(qs)
        s = HistorialAsignacionSerializer(page or qs, many=True)
        return self.get_paginated_response(s.data) if page is not None else Response(s.data)

    # ---------- HISTORIAL: EXPORT (CSV/XLSX, solo admin) ----------
    @action(detail=False, methods=["get", "post"], url_path="historial/export")
    def historial_export(self, request):
        u = request.user
        if getattr(u, "rol", None) != "administrador":
            return Response({"detail": "Solo administrador puede exportar historial."}, status=403)

        qs = self._historial_filtered_qs(request).order_by("asignacion_id", "created_at", "id")
        fmt = (getattr(request, "data", None) or {}).get("format")
        if not fmt:
            fmt = request.query_params.get("format", "xlsx")
        fmt = (fmt or "xlsx").lower()

        headers = ["historial_id","asignacion_id","direccion","comuna","marca","tecnologia","fecha","bloque","accion","detalles","usuario_email","creado"]

        if fmt == "csv":
            buff = io.StringIO()
            writer = csv.writer(buff)
            writer.writerow(headers)
            for h in qs.iterator():
                writer.writerow([
                    h.id,
                    h.asignacion_id,
                    getattr(h.asignacion, "direccion", ""),
                    getattr(h.asignacion, "comuna", ""),
                    getattr(h.asignacion, "marca", ""),
                    getattr(h.asignacion, "tecnologia", ""),
                    getattr(h.asignacion, "fecha", "") or "",
                    getattr(h.asignacion, "reagendado_bloque", "") or "",
                    h.accion,
                    h.detalles,
                    getattr(h.usuario, "email", ""),
                    h.created_at.isoformat(),
                ])
            resp = HttpResponse(buff.getvalue(), content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = 'attachment; filename="historial.csv"'
            return resp

        wb = Workbook()
        ws = wb.active
        ws.title = "Historial"
        ws.append(headers)
        for h in qs.iterator():
            ws.append([
                h.id,
                h.asignacion_id,
                getattr(h.asignacion, "direccion", ""),
                getattr(h.asignacion, "comuna", ""),
                getattr(h.asignacion, "marca", ""),
                getattr(h.asignacion, "tecnologia", ""),
                getattr(h.asignacion, "fecha", "") or "",
                getattr(h.asignacion, "reagendado_bloque", "") or "",
                h.accion,
                h.detalles,
                getattr(h.usuario, "email", ""),
                h.created_at.isoformat(),
            ])
        out = io.BytesIO()
        wb.save(out)
        resp = HttpResponse(out.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = 'attachment; filename="historial.xlsx"'
        return resp

    # === CARGA CSV/XLSX (planning semanal) ===
    @extend_schema(request=CargaCSVSerializer)
    @action(
        detail=False,
        methods=["post"],
        url_path="cargar_csv",
        parser_classes=[MultiPartParser, FormParser],
        serializer_class=CargaCSVSerializer,
    )
    def cargar_csv(self, request):
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

    # ---------- DESASIGNAR (ADMIN) ----------
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

    # ---------- ESTADO DEL CLIENTE (Q5) ----------
    @action(detail=True, methods=["post"], url_path="estado_cliente")
    def estado_cliente(self, request, pk=None):
        """
        Q5 Estado del Cliente:
        - autoriza -> VISITADA
        - sin_moradores | rechaza | contingencia | masivo -> CANCELADA
        - reagendo -> requiere fecha/bloque -> REAGENDADA + notificación real
        """
        asignacion = self.get_object()
        data = request.data or {}
        estado_cliente = (data.get("estado_cliente") or "").strip().lower()

        valid = {"autoriza", "sin_moradores", "rechaza", "contingencia", "masivo", "reagendo"}
        if estado_cliente not in valid:
            return Response({"detail": "estado_cliente inválido."}, status=400)

        with transaction.atomic():
            if estado_cliente == "autoriza":
                asignacion.estado = "VISITADA"
                asignacion.save(update_fields=["estado", "updated_at"])

                HistorialAsignacion.objects.create(
                    asignacion=asignacion,
                    accion="CERRADA" if hasattr(HistorialAsignacion.Accion, "CERRADA") else "ESTADO_CLIENTE",
                    detalles="Estado cliente = autoriza (asignación VISITADA).",
                    usuario=request.user,
                )

            elif estado_cliente in {"sin_moradores", "rechaza", "contingencia", "masivo"}:
                asignacion.estado = "CANCELADA"
                asignacion.save(update_fields=["estado", "updated_at"])

                HistorialAsignacion.objects.create(
                    asignacion=asignacion,
                    accion="ESTADO_CLIENTE",
                    detalles=f"Estado cliente = {estado_cliente} (asignación CANCELADA).",
                    usuario=request.user,
                )

            else:  # reagendo
                f_raw = data.get("reagendado_fecha")
                reag_fecha = _parse_date(f_raw)
                reag_bloque = _normalize_bloque(data.get("reagendado_bloque"))
                if not reag_fecha or not reag_bloque:
                    return Response(
                        {"estado_cliente": ["Este campo es requerido."], "detail": "Debe indicar fecha y bloque."},
                        status=400
                    )
                if reag_fecha < timezone.localdate():
                    return Response({"detail": "La fecha reagendada no puede ser pasada."}, status=400)

                asignacion.reagendado_fecha = reag_fecha
                asignacion.reagendado_bloque = reag_bloque
                asignacion.estado = "REAGENDADA"
                asignacion.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado", "updated_at"])

                HistorialAsignacion.objects.create(
                    asignacion=asignacion,
                    accion="REAGENDADA",
                    detalles=f"Reagendada desde auditoría a {reag_fecha} {reag_bloque}",
                    usuario=request.user,
                )

                # ---- Registrar y ENVIAR notificación real por email ----
                destino = getattr(asignacion.asignado_a, "email", "") or ""
                notif = Notificacion.objects.create(
                    asignacion_id=asignacion.id,
                    canal=Notificacion.Canal.EMAIL,
                    tipo="reagendamiento",
                    destino=destino,  # si está vacío, notify no envía
                    asunto=f"Reagendamiento Asignación #{asignacion.id}",
                    payload={
                        "asignacion_id": asignacion.id,
                        "direccion": asignacion.direccion,
                        "comuna": asignacion.comuna,
                        "reagendado_fecha": reag_fecha.isoformat(),
                        "reagendado_bloque": reag_bloque,
                        "tecnico_id": getattr(request.user, "id", None),
                        "tecnico_email": destino,
                    },
                    status=Notificacion.Estado.PENDING,
                )
                enviar_notificacion_real(notif)

        return Response(self.get_serializer(asignacion).data)

    # ---------- MÉTRICAS (resumen) ----------
    @action(detail=False, methods=["get"], url_path="metrics/resumen")
    def metrics_resumen(self, request):
        qs = DireccionAsignada.objects.all()
        p = request.query_params

        if p.get("fecha__gte"): qs = qs.filter(fecha__gte=p["fecha__gte"])
        if p.get("fecha__lte"): qs = qs.filter(fecha__lte=p["fecha__lte"])
        if p.get("tecnico_id"): qs = qs.filter(asignado_a_id=p["tecnico_id"])
        if p.get("zona"): qs = qs.filter(zona=p["zona"])
        if p.get("comuna"): qs = qs.filter(comuna=p["comuna"])
        if p.get("marca"): qs = qs.filter(marca=p["marca"])
        if p.get("tecnologia"): qs = qs.filter(tecnologia=p["tecnologia"])

        total = qs.count()
        c = lambda s: qs.filter(estado=s).count()
        pend, asig, vis, canc, reag = (c("PENDIENTE"), c("ASIGNADA"), c("VISITADA"), c("CANCELADA"), c("REAGENDADA"))
        pct = lambda n: round(100.0 * n / total, 1) if total else 0.0
        return Response({
            "total": total,
            "pendientes": pend,
            "asignadas": asig,
            "visitadas": vis,
            "canceladas": canc,
            "reagendadas": reag,
            "pct_visitadas": pct(vis),
            "pct_reagendadas": pct(reag),
        })

    # ---------- MÉTRICAS (por técnico autenticado o pasado por query) ----------
    @action(detail=False, methods=["get"], url_path="metrics/tecnico")
    def metrics_tecnico(self, request):
        qs = DireccionAsignada.objects.all()
        p = request.query_params
        u = request.user

        tecnico_id = p.get("tecnico_id")
        if getattr(u, "rol", None) == "tecnico":
            tecnico_id = u.id
        if tecnico_id:
            qs = qs.filter(asignado_a_id=tecnico_id)

        if p.get("fecha__gte"): qs = qs.filter(fecha__gte=p["fecha__gte"])
        if p.get("fecha__lte"): qs = qs.filter(fecha__lte=p["fecha__lte"])
        if p.get("zona"): qs = qs.filter(zona=p["zona"])
        if p.get("comuna"): qs = qs.filter(comuna=p["comuna"])
        if p.get("marca"): qs = qs.filter(marca=p["marca"])
        if p.get("tecnologia"): qs = qs.filter(tecnologia=p["tecnologia"])

        total = qs.count()
        c = lambda s: qs.filter(estado=s).count()
        pend, asig, vis, canc, reag = (c("PENDIENTE"), c("ASIGNADA"), c("VISITADA"), c("CANCELADA"), c("REAGENDADA"))
        pct = lambda n: round(100.0 * n / total, 1) if total else 0.0
        return Response({
            "total": total,
            "pendientes": pend,
            "asignadas": asig,
            "visitadas": vis,
            "canceladas": canc,
            "reagendadas": reag,
            "pct_visitadas": pct(vis),
            "pct_reagendadas": pct(reag),
        })

    # ---------- MÉTRICAS: EXPORT (CSV/XLSX, solo admin) ----------
    @action(detail=False, methods=["get", "post"], url_path="metrics/export")
    def metrics_export(self, request):
        if getattr(request.user, "rol", None) != "administrador":
            return Response({"detail": "Solo administrador puede exportar métricas."}, status=403)

        resumen = self.metrics_resumen(request).data
        fmt = (getattr(request, "data", None) or {}).get("format")
        if not fmt:
            fmt = request.query_params.get("format", "xlsx")
        fmt = (fmt or "xlsx").lower()

        headers = ["total","pendientes","asignadas","visitadas","canceladas","reagendadas","pct_visitadas","pct_reagendadas"]

        if fmt == "csv":
            buff = io.StringIO()
            w = csv.writer(buff)
            w.writerow(headers)
            w.writerow([
                resumen["total"], resumen["pendientes"], resumen["asignadas"],
                resumen["visitadas"], resumen["canceladas"], resumen["reagendadas"],
                resumen["pct_visitadas"], resumen["pct_reagendadas"]
            ])
            resp = HttpResponse(buff.getvalue(), content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = 'attachment; filename=\"metricas_resumen.csv\"'
            return resp

        wb = Workbook()
        ws = wb.active
        ws.title = "Resumen"
        ws.append(headers)
        ws.append([
            resumen["total"], resumen["pendientes"], resumen["asignadas"],
            resumen["visitadas"], resumen["canceladas"], resumen["reagendadas"],
            resumen["pct_visitadas"], resumen["pct_reagendadas"]
        ])
        out = io.BytesIO()
        wb.save(out)
        resp = HttpResponse(out.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resp["Content-Disposition"] = 'attachment; filename=\"metricas_resumen.xlsx\"'
        return resp

    # ---------- MÉTRICAS: SERIE (datos listos para gráficos) ----------
    @action(detail=False, methods=["get"], url_path="metrics/serie")
    def metrics_serie(self, request):
        """
        Devuelve serie por día para Visitadas, Reagendadas y Canceladas
        (según filtros de fecha/zona/tecnico/etc.) usando asignacion.fecha.
        """
        qs = DireccionAsignada.objects.all()
        p = request.query_params

        if p.get("fecha__gte"): qs = qs.filter(fecha__gte=p["fecha__gte"])
        if p.get("fecha__lte"): qs = qs.filter(fecha__lte=p["fecha__lte"])
        if p.get("tecnico_id"): qs = qs.filter(asignado_a_id=p["tecnico_id"])
        if p.get("zona"): qs = qs.filter(zona=p["zona"])
        if p.get("comuna"): qs = qs.filter(comuna=p["comuna"])
        if p.get("marca"): qs = qs.filter(marca=p["marca"])
        if p.get("tecnologia"): qs = qs.filter(tecnologia=p["tecnologia"])

        def serie_por_estado(estado: str):
            base = qs.filter(estado=estado, fecha__isnull=False)
            agg = (base.annotate(d=TruncDate("fecha"))
                        .values("d").annotate(c=Count("id")).order_by("d"))
            return {a["d"].isoformat(): a["c"] for a in agg}

        v = serie_por_estado("VISITADA")
        r = serie_por_estado("REAGENDADA")
        c = serie_por_estado("CANCELADA")

        fechas = sorted(set(v.keys()) | set(r.keys()) | set(c.keys()))
        data = {
            "labels": fechas,
            "series": {
                "visitadas": [v.get(d, 0) for d in fechas],
                "reagendadas": [r.get(d, 0) for d in fechas],
                "canceladas": [c.get(d, 0) for d in fechas],
            }
        }
        return Response(data)
