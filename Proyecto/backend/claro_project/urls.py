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

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuarios")
router.register(r"asignaciones", DireccionAsignadaViewSet, basename="asignaciones")
router.register(r"auditorias", AuditoriaVisitaViewSet, basename="auditorias")

# SPA con cookie CSRF al cargar la raíz
SpaView = method_decorator(ensure_csrf_cookie, name="dispatch")(TemplateView)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API REST
    path("api/", include(router.urls)),

    # Auth (elige UNO de los dos enfoques; aquí dejo el explícito)
    # path("auth/", include("usuarios.auth_urls")),  # <- Si usas este, borra las rutas explícitas de abajo
    path("auth/register", RegisterView.as_view()),
    path("auth/login",    LoginView.as_view()),
    path("auth/refresh",  RefreshCookieView.as_view()),
    path("auth/logout",   LogoutView.as_view()),
    path("auth/me",       MeView.as_view()),
    path("auth/csrf",     CsrfTokenView.as_view()),

    # SPA en la raíz
    path("", TemplateView.as_view(template_name="index.html"), name="spa"),
    re_path(r"^(?!api/|admin/|auth/|static/|media/).*$",
            TemplateView.as_view(template_name="index.html")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
