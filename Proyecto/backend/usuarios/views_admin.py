# usuarios/views_admin.py
from django.db import connection
from django.db.utils import ProgrammingError, DatabaseError
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action

from core.permissions import AdminOnly
from core.models import LogSistema
from .models import Usuario, UsuarioSistema
from .serializers import (
    UsuarioSerializer,
    UsuarioSistemaListSerializer,
    UsuarioListSerializer,
    UsuarioRoleUpdateSerializer,
)

def _vista_usuarios_sistema_disponible() -> bool:
    """
    Devuelve True si la vista usuarios_sistema existe y es consultable.
    No levanta excepción hacia arriba.
    """
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1 FROM usuarios_sistema LIMIT 1;")
        return True
    except Exception:
        return False


class AdminUsuarioViewSet(viewsets.ModelViewSet):
    """
    Backoffice de usuarios (solo rol=administrador).
    - GET /api/admin/usuarios            -> listar/buscar/filtrar/ordenar
    - POST /api/admin/usuarios           -> crear
    - PUT/PATCH /api/admin/usuarios/:id  -> editar
    - DELETE /api/admin/usuarios/:id     -> suspender (is_active=False)
    - PUT /api/admin/usuarios/:id/rol    -> actualizar solo el rol
    """
    permission_classes = [IsAuthenticated, AdminOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        "rol": ["exact"],
        "is_active": ["exact"],
    }
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["id", "date_joined", "email", "first_name", "last_name", "rol", "is_active"]
    ordering = ["-date_joined", "-id"]

    # Para create/retrieve/update/destroy usamos la tabla base:
    queryset = Usuario.objects.all().order_by("-date_joined", "-id")
    serializer_class = UsuarioSerializer

    # === Fallback sólido: decide el origen del listado ===
    def get_queryset(self):
        if self.action == "list":
            if _vista_usuarios_sistema_disponible():
                try:
                    return UsuarioSistema.objects.all().order_by("-date_joined", "-id")
                except (ProgrammingError, DatabaseError):
                    pass
            return Usuario.objects.all().order_by("-date_joined", "-id")
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == "list":
            if _vista_usuarios_sistema_disponible():
                return UsuarioSistemaListSerializer
            return UsuarioListSerializer
        return UsuarioSerializer

    # Hooks para log de acciones
    def perform_create(self, serializer):
        obj = serializer.save()
        LogSistema.objects.create(
            usuario=self.request.user,
            accion=getattr(LogSistema.Accion, "USER_CREATE", "USER_CREATE"),
            detalle=f"Creó usuario {obj.email} (rol={obj.rol}, activo={obj.is_active})",
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        LogSistema.objects.create(
            usuario=self.request.user,
            accion=getattr(LogSistema.Accion, "USER_UPDATE", "USER_UPDATE"),
            detalle=f"Actualizó usuario {obj.email} (rol={obj.rol}, activo={obj.is_active})",
        )

    # DELETE = "suspender" (soft-delete)
    def perform_destroy(self, instance):
        """
        En esta API, DELETE = suspender (soft-delete).
        No borramos el registro: solo marcamos is_active=False.
        """
        if instance.is_active:
            instance.is_active = False
            instance.save(update_fields=["is_active"])
            # Usa USER_DEACTIVATE si lo tienes definido; si no, deja USER_DELETE.
            LogSistema.objects.create(
                usuario=self.request.user,
                accion=getattr(LogSistema.Accion, "USER_DEACTIVATE", "USER_DELETE"),
                detalle=f"Desactivó usuario {instance.email}",
            )

    # === NUEVO: actualizar SOLO el rol ===
    @action(detail=True, methods=["put"], url_path="rol")
    def actualizar_rol(self, request, pk=None):
        """PUT /api/admin/usuarios/:id/rol  -> { "rol": "administrador" | "tecnico" }"""
        user = self.get_object()
        ser = UsuarioRoleUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        nuevo_rol = ser.validated_data["rol"]
        if user.rol == nuevo_rol:
            return Response({"detail": "El rol ya es el indicado.", "rol": user.rol})

        user.rol = nuevo_rol
        user.save(update_fields=["rol"])
        LogSistema.objects.create(
            usuario=request.user,
            accion=LogSistema.Accion.USER_ROLE_UPDATE,
            detalle=f"Cambió rol de {user.email} a {nuevo_rol}",
        )

        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "rol": user.rol,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
        })
