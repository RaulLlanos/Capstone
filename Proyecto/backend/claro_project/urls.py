# claro_project/urls.py
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

# ✅ Import correcto (solo este)
from asignaciones.views import DireccionAsignadaViewSet
from auditoria.views import AuditoriaVisitaViewSet, IssueViewSet

router = routers.DefaultRouter()
router.register(r'usuarios', usuarios_views.UsuarioViewSet, basename='usuarios')

# Asignaciones / Auditorías
router.register(r'asignaciones', DireccionAsignadaViewSet, basename='asignaciones')
router.register(r'auditorias',   AuditoriaVisitaViewSet, basename='auditorias')
router.register(r'issues',       IssueViewSet,           basename='issues')

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
    path('auth/csrf',     CsrfTokenView.as_view(), name='auth-csrf'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
