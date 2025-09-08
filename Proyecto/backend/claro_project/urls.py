# claro_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from rest_framework import routers

from django.conf import settings
from django.conf.urls.static import static

from usuarios import views as usuarios_views
from usuarios.auth_views import RegisterView, LoginView, MeView, LogoutView, RefreshCookieView, CsrfTokenView

from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet, IssueViewSet

from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)

router = routers.DefaultRouter()
router.register(r'usuarios', usuarios_views.UsuarioViewSet)
router.register(r'tecnicos', usuarios_views.TecnicoViewSet)
router.register(r'visitas', usuarios_views.VisitaViewSet)
router.register(r'reagendamientos', usuarios_views.ReagendamientoViewSet)
router.register(r'historial', usuarios_views.HistorialVisitaViewSet)
router.register(r'evidencias', usuarios_views.EvidenciaServicioViewSet)

router.register(r'asignaciones', DireccionAsignadaViewSet, basename='asignaciones')
router.register(r'auditorias',   AuditoriaVisitaViewSet,   basename='auditorias')
router.register(r'issues',       IssueViewSet,             basename='issues')

def gracias(request):
    html = """
    <!doctype html><html lang="es"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Gracias</title>
    <style>:root{color-scheme:light dark}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f6f7fb;font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Helvetica Neue,Arial}</style>
    </head><body><div style="background:#fff;padding:28px 24px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.08);text-align:center;max-width:520px">
    <h1>¡Gracias!</h1><p>Tu gestión fue registrada correctamente.</p><a href="/docs">Volver a la API</a></div></body></html>
    """
    return HttpResponse(html)

urlpatterns = [
    path('', lambda r: JsonResponse({
        'name': 'ClaroVTR API',
        'version': '1.0',
        'api_root': '/api/',
        'auth': {'register': '/auth/register', 'login': '/auth/login', 'me': '/auth/me'}
    }), name='home'),

    path('gracias/', gracias, name='gracias'),

    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # Auth (+ CSRF)
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login',    LoginView.as_view(),    name='auth-login'),
    path('auth/refresh',  RefreshCookieView.as_view(), name='auth-refresh'),
    path('auth/logout',   LogoutView.as_view(),   name='auth-logout'),
    path('auth/me',       MeView.as_view(),       name='auth-me'),
    path('auth/csrf',     CsrfTokenView.as_view(), name='auth-csrf'),  # NUEVO

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
