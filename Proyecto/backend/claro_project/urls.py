from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from core.views import gracias
from usuarios import views as usuarios_views
from usuarios.auth_views import (
    RegisterView, LoginView, MeView, LogoutView, RefreshCookieView, CsrfTokenView
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from usuarios.views_admin import AdminUsuarioViewSet 
from core.views_health import Healthz, Readyz

router = routers.DefaultRouter()
router.register(r'usuarios', usuarios_views.UsuarioViewSet, basename='usuarios')
router.register(r'asignaciones', DireccionAsignadaViewSet, basename='asignaciones')
router.register(r'auditorias', AuditoriaVisitaViewSet, basename='auditorias')
router.register(r'admin/usuarios', AdminUsuarioViewSet, basename='admin-usuarios')

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

    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login',    LoginView.as_view(),    name='auth-login'),
    path('auth/refresh',  RefreshCookieView.as_view(), name='auth-refresh'),
    path('auth/logout',   LogoutView.as_view(),   name='auth-logout'),
    path('auth/me',       MeView.as_view(),       name='auth-me'),
    path('auth/csrf',     CsrfTokenView.as_view(), name='auth-csrf'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("core.urls_admin")),
    path("healthz", Healthz.as_view()),
    path("readyz", Readyz.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
