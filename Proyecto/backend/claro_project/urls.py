from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import routers

from django.conf import settings
from django.conf.urls.static import static

# Vistas de apps
from usuarios import views as usuarios_views
from usuarios.auth_views import RegisterView, LoginView, MeView, LogoutView, RefreshCookieView

from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet, IssueViewSet

# Docs (drf-spectacular)
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)

router = routers.DefaultRouter()

# usuarios (legacy + admin)
router.register(r'usuarios', usuarios_views.UsuarioViewSet)
router.register(r'tecnicos', usuarios_views.TecnicoViewSet)
router.register(r'visitas', usuarios_views.VisitaViewSet)
router.register(r'reagendamientos', usuarios_views.ReagendamientoViewSet)
router.register(r'historial', usuarios_views.HistorialVisitaViewSet)
router.register(r'evidencias', usuarios_views.EvidenciaServicioViewSet)

# nuevas
router.register(r'asignaciones', DireccionAsignadaViewSet, basename='asignaciones')
router.register(r'auditorias',   AuditoriaVisitaViewSet,   basename='auditorias')
router.register(r'issues',       IssueViewSet,             basename='issues')

urlpatterns = [
    # Home / health
    path('', lambda r: JsonResponse({
        'name': 'ClaroVTR API',
        'version': '1.0',
        'api_root': '/api/',
        'auth': {'register': '/auth/register', 'login': '/auth/login', 'me': '/auth/me'}
    }), name='home'),

    # Admin
    path('admin/', admin.site.urls),

    # API REST
    path('api/', include(router.urls)),

    # Auth (HU-1/HU-3)
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login',    LoginView.as_view(),    name='auth-login'),
    path('auth/refresh',  RefreshCookieView.as_view(), name='auth-refresh'),
    path('auth/logout',   LogoutView.as_view(),   name='auth-logout'), 
    path('auth/me',       MeView.as_view(),       name='auth-me'),

    # DRF login de sesión (opcional)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # === Documentación OpenAPI/Swagger/ReDoc ===
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]

# Media (fotos)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
