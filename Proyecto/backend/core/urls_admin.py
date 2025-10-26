# core/urls_admin.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_admin import ConfiguracionAdminViewSet, LogsAdminViewSet

router = DefaultRouter()
router.register(r"admin/configuracion", ConfiguracionAdminViewSet, basename="admin-configuracion")
router.register(r"admin/logs", LogsAdminViewSet, basename="admin-logs")

urlpatterns = [
    path("", include(router.urls)),
]
