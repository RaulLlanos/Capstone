# core/views.py
from django.http import HttpResponse
from django.utils.html import escape
from rest_framework import viewsets, permissions
from core.models import Notificacion, LogSistema
from core.serializers import NotificacionSerializer, LogSistemaSerializer
from django.shortcuts import render, redirect
from auditoria.models import AuditoriaVisita
from django.db.models import Max
from django.core.paginator import Paginator


class NotificacionViewSet(viewsets.ModelViewSet):
    """
    CRUD de notificaciones.
    Permiso básico: autenticado (puedes cambiar a IsAdminUser si quieres).
    """
    queryset = Notificacion.objects.all().order_by("-id")
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

class LogSistemaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo lectura de logs del sistema (útil para auditar errores 4xx/5xx).
    """
    queryset = LogSistema.objects.all().order_by("-id")
    serializer_class = LogSistemaSerializer
    permission_classes = [permissions.IsAuthenticated]

ESTADOS_LABEL = {
    "autoriza": "Autoriza a ingresar",
    "sin_moradores": "Sin Moradores",
    "rechaza": "Rechaza",
    "contingencia": "Contingencia externa",
    "masivo": "Incidencia Masivo ClaroVTR",
    "reagendo": "Reagendó",
}

def gracias(request):
    estado_code = request.GET.get("estado", "") or ""
    estado_safe = escape(estado_code)
    estado_label = ESTADOS_LABEL.get(estado_code, estado_safe)

    asignacion_id = escape(request.GET.get("id", "") or "")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Gracias - ClaroVTR</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex,nofollow">
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; margin: 0; }}
    .wrap {{ min-height: 100vh; display: grid; place-items: center; background: #f7f7f8; }}
    .card {{
      background: white; padding: 28px; border-radius: 16px; width: 100%; max-width: 520px;
      box-shadow: 0 10px 30px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.08);
      border: 1px solid #eee;
    }}
    h1 {{ margin: 0 0 8px; font-size: 22px; }}
    p {{ margin: 0 0 8px; color: #444; }}
    .muted {{ color: #777; font-size: 14px; }}
    .brand {{ color: #e4002b; font-weight: 700; }}
    .foot {{ margin-top: 14px; font-size: 12px; color: #999; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>¡Gracias!</h1>
      <p>Registramos el resultado de la visita{(" #" + asignacion_id) if asignacion_id else ""}.</p>
      {f'<p class="muted">Estado seleccionado: <strong>{estado_label}</strong></p>' if estado_label else ""}
      <p class="muted">Equipo <span class="brand">ClaroVTR</span></p>
      <div class="foot">Puede cerrar esta página.</div>
    </div>
  </div>
</body>
</html>
"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")

def _display_user(u):
    if not u:
        return "—"
    name = f"{(u.first_name or '').strip()} {(u.last_name or '').strip()}".strip()
    if name:
        return name
    if u.email:
        return u.email.split("@")[0]
    return f"Tec#{u.id}"

def auditoria_detalle(request, pk: int):
    aid = request.GET.get("aid")     # fuerza “audit id”
    asid = request.GET.get("asid")   # fuerza “asignación id”

    obj = None

    # 1) Si llega aid en query ⇒ intenta por id de auditoría
    if aid and str(aid).isdigit():
        obj = (AuditoriaVisita.objects
               .select_related("asignacion","tecnico")
               .filter(pk=int(aid)).first())

    # 2) Si no, intenta por path param como id de auditoría
    if not obj:
        obj = (AuditoriaVisita.objects
               .select_related("asignacion","tecnico")
               .filter(pk=pk).first())

    # 3) Si aún no, prueba como id de asignación (query o path)
    if not obj:
        try_asig = int(asid) if asid and str(asid).isdigit() else pk
        obj = (AuditoriaVisita.objects
               .select_related("asignacion","tecnico")
               .filter(asignacion_id=try_asig)
               .order_by("-created_at","-id")
               .first())

    if not obj:
        return render(request, "admin_auditorias/detalle.html",
                      {"error": "No se encontró auditoría para ese identificador."}, status=404)

    tec_obj = obj.tecnico or getattr(obj.asignacion, "asignado_a", None)
    tec_label = _display_user(tec_obj)
    return render(request, "admin_auditorias/detalle.html", {"a": obj, "tec_label": tec_label})

def auditorias_list(request):
    """
    /admin/auditorias/?mode=all            -> todas, más nuevas arriba
    /admin/auditorias/?mode=last           -> solo la última por asignación
    /admin/auditorias/?asignacion=61       -> todas las de esa asignación (más nuevas arriba)
    Se puede combinar con page=? para paginar.
    """
    mode = request.GET.get("mode", "all")
    asignacion = request.GET.get("asignacion")

    qs = (AuditoriaVisita.objects
          .select_related("asignacion", "tecnico"))

    # Filtro opcional por asignación (muestra TODAS las de esa dirección, más nuevas arriba)
    if asignacion:
        qs = qs.filter(asignacion_id=asignacion)

    if mode == "last":
        # Una por asignación (la última)
        last_ids = (AuditoriaVisita.objects
                    .values("asignacion_id")
                    .annotate(last_id=Max("id"))
                    .values_list("last_id", flat=True))
        qs = qs.filter(id__in=list(last_ids)).order_by("-created_at", "-id")
    else:
        # TODAS, más nuevas arriba
        qs = qs.order_by("-created_at", "-id")

    # Paginación server-side (no rompe nada y evita páginas gigantes)
    paginator = Paginator(qs, 50)  # 50 por página
    page_obj = paginator.get_page(request.GET.get("page", 1))

    ctx = {
        "auditorias": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "mode": mode,
        "asignacion": asignacion,
    }
    return render(request, "admin_auditorias/lista.html", ctx)
