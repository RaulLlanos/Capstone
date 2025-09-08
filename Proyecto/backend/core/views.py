# core/views.py
from django.http import HttpResponse

def gracias(request):
    estado = request.GET.get("estado", "")
    asignacion_id = request.GET.get("id", "")
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Gracias - ClaroVTR</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
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
      {f'<p class="muted">Estado seleccionado: <strong>{estado}</strong></p>' if estado else ""}
      <p class="muted">Equipo <span class="brand">ClaroVTR</span></p>
      <div class="foot">Puede cerrar esta página.</div>
    </div>
  </div>
</body>
</html>
"""
    return HttpResponse(html)
