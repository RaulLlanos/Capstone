# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import NotificacionViewSet, LogSistemaViewSet

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificaciones')
router.register(r'logs', LogSistemaViewSet, basename='logs')

urlpatterns = [
    path('', include(router.urls)),
]
