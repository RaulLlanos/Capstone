# Proyecto/backend/claro_project/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles import finders

from rest_framework.routers import DefaultRouter

# Routers de tus apps
from usuarios.views import UsuarioViewSet
from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet

# Endpoints de auth (cookies JWT) si ya los tienes
from usuarios.auth_views import (
    RegisterView, LoginView, RefreshCookieView, LogoutView, MeView, CsrfTokenView
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'asignaciones', DireccionAsignadaViewSet, basename='asignacion')
router.register(r'auditorias', AuditoriaVisitaViewSet, basename='auditoria')


def _load_spa_index_bytes():
    """
    Devuelve el contenido de static 'frontend/index.html'.
    Primero intenta via storage.path (producción con collectstatic),
    si no, usa finders (útil en DEBUG).
    """
    rel = "frontend/index.html"
    try:
        # Producción: ManifestStaticFilesStorage/WhiteNoise
        full = staticfiles_storage.path(rel)
    except Exception:
        full = finders.find(rel)
    if not full:
        return None
    with open(full, "rb") as f:
        return f.read()


def spa_index(request, path=""):
    """
    Fallback del SPA: cualquier ruta que no sea /api, /admin, /auth, /static, /media
    devuelve el index.html del build de React (Vite).
    """
    content = _load_spa_index_bytes()
    if not content:
        return HttpResponseNotFound(
            "index.html no encontrado. ¿Ejecutaste el build del frontend y 'collectstatic'?"
        )
    return HttpResponse(content, content_type="text/html; charset=utf-8")


urlpatterns = [
    path('admin/', admin.site.urls),

    # API DRF
    path('api/', include(router.urls)),

    # Auth por cookies (respetando tus paths)
    path('auth/register', RegisterView.as_view()),
    path('auth/login',    LoginView.as_view()),
    path('auth/refresh',  RefreshCookieView.as_view()),
    path('auth/logout',   LogoutView.as_view()),
    path('auth/me',       MeView.as_view()),
    path('auth/csrf',     CsrfTokenView.as_view()),
]

# Media en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Fallback del SPA (debe ir AL FINAL)
urlpatterns += [
    re_path(r'^(?!api/|admin/|auth/|static/|media/).*$', spa_index),
    path('', spa_index),  # raíz
]
