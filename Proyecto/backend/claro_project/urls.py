# Proyecto/backend/claro_project/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.routers import DefaultRouter

from usuarios.views import UsuarioViewSet
from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet

from usuarios.auth_views import (
    RegisterView, LoginView, RefreshCookieView,
    LogoutView, MeView, CsrfTokenView,
)

# DRF router
router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuarios")
router.register(r"asignaciones", DireccionAsignadaViewSet, basename="asignaciones")
router.register(r"auditorias", AuditoriaVisitaViewSet, basename="auditorias")

# SPA (colocamos ensure_csrf_cookie para que el CSRFTOKEN quede listo al cargar / )
SpaView = method_decorator(ensure_csrf_cookie, name="dispatch")(TemplateView)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API REST
    path("api/", include(router.urls)),

    # Auth (cookies HttpOnly)
    path("auth/register", RegisterView.as_view()),
    path("auth/login",    LoginView.as_view()),
    path("auth/refresh",  RefreshCookieView.as_view()),
    path("auth/logout",   LogoutView.as_view()),
    path("auth/me",       MeView.as_view()),
    path("auth/csrf",     CsrfTokenView.as_view()),

    # SPA en la raíz
    path("", SpaView.as_view(template_name="index.html"), name="spa"),
    # Fallback SPA para rutas de frontend (evita 404 al refrescar en /dashboard, etc.)
    re_path(r"^(?!api/|auth/|admin/|static/|media/).*$",
            SpaView.as_view(template_name="index.html")),
]

# Static/media en DEBUG (en prod WhiteNoise sirve /static)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
