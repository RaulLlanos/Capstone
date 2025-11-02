# backend/claro_project/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
from django.views.generic import TemplateView, RedirectView

from rest_framework.routers import DefaultRouter

from usuarios.views import UsuarioViewSet
from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet

from usuarios.auth_views import (
    RegisterView,
    LoginView,
    RefreshCookieView,
    LogoutView,
    MeView,
    CsrfTokenView,
)

router = DefaultRouter()
router.register(r"usuarios", UsuarioViewSet, basename="usuarios")
router.register(r"asignaciones", DireccionAsignadaViewSet, basename="asignaciones")
router.register(r"auditorias", AuditoriaVisitaViewSet, basename="auditorias")

def index_view(_request):
    # fallback simple si aún no has copiado tu SPA; sirve para “/”
    return HttpResponse("ClaroVTR API", content_type="text/plain")

urlpatterns = [
    path("", RedirectView.as_view(url="/login/", permanent=False)),
    path("admin/", admin.site.urls),

    # Ruta explícita para la vista de login (HTML)
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),

    # API DRF
    path("api/", include(router.urls)),

    # AUTH (cookies JWT)
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", RefreshCookieView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("auth/csrf", CsrfTokenView.as_view()),

    # Raíz mínima
    path("", index_view),
]

# Static en desarrollo (WhiteNoise cubre en prod)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Fallback SPA (si copiaste /frontend/dist → /static/frontend/)
urlpatterns += [
    re_path(r"^(?!api/|admin/|auth/|static/|media/).*$", index_view),
]
