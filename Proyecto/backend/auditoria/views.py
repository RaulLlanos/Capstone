# auditoria/views.py
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated  # ← import correcto
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer
from usuarios.models import Usuario  # ← para el endpoint /tecnicos


class IsAdminOrTechOwner(permissions.BasePermission):
    """
    - 'administrador': acceso total.
    - 'tecnico': solo auditorías donde es el técnico asignado (auditoria.tecnico_id == user.id)
      o donde la asignación está asignada a él (auditoria.asignacion.asignado_a_id == user.id).
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not u.is_authenticated:
            return False
        return getattr(u, "rol", None) in ("administrador", "tecnico")

    def has_object_permission(self, request, view, obj: AuditoriaVisita):
        rol = getattr(request.user, "rol", None)
        if rol == "administrador":
            return True
        if rol == "tecnico":
            return (
                (obj.tecnico_id == request.user.id) or
                (obj.asignacion and obj.asignacion.asignado_a_id == request.user.id)
            )
        return False


class AuditoriaVisitaViewSet(viewsets.ModelViewSet):
    """
    CRUD de auditorías.
    - Técnico: sólo las suyas (dueño directo o dueño de la asignación).
    - Administrador: todas.

    Filtros:
      - customer_status
      - asignacion__asignado_a (id técnico)
      - tecnico (id técnico directo en la auditoría)  ← alias añadido, por si el FE lo usa
      - asignacion__comuna, asignacion__zona
      - created_at__gte / __lte
    """
    queryset = (
        AuditoriaVisita.objects
        .select_related("asignacion", "tecnico", "asignacion__asignado_a")
        .all()
        .order_by("-created_at", "-id")
    )
    serializer_class = AuditoriaVisitaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrTechOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "customer_status": ["exact", "in"],
        "asignacion__asignado_a": ["exact"],
        "tecnico": ["exact"],                  # <—— NUEVO alias “a prueba de balas”
        "asignacion__comuna": ["exact"],
        "asignacion__zona": ["exact"],
        "created_at": ["gte", "lte"],
    }
    search_fields = ["asignacion__direccion", "asignacion__rut_cliente", "asignacion__comuna"]
    ordering_fields = ["created_at", "asignacion__comuna", "asignacion__zona", "tecnico__first_name", "tecnico__last_name", "asignacion__asignado_a__first_name", "asignacion__asignado_a__last_name"]

    def get_queryset(self):
        u = self.request.user
        rol = getattr(u, "rol", None)

        # Usa el queryset base (ya tiene select_related + order_by)
        qs = self.queryset

        if rol == "administrador":
            return qs

        if rol == "tecnico":
            return qs.filter(
                Q(tecnico_id=u.id) |
                Q(asignacion__asignado_a_id=u.id)
            )

        return qs.none()

    # ---------------- helpers display name ----------------
    @staticmethod
    def _display_name(user: Usuario | None) -> str:
        """
        Devuelve 'Nombre Apellido' si existe; si no, local-part del email; si no, Tec#ID.
        """
        if not user:
            return ""
        fn = (user.first_name or "").strip()
        ln = (user.last_name or "").strip()
        full = f"{fn} {ln}".strip()
        if full:
            return full
        email = (user.email or "").strip()
        if email:
            local = email.split("@")[0]
            if local:
                return local
        return f"Tec#{user.id}"

    # ---------------- endpoint para poblar el combo de técnicos en FE ----------------
    @action(detail=False, methods=["get"], url_path="tecnicos")
    def tecnicos(self, request):
        """
        Devuelve los técnicos que aparecen en las auditorías (dueño directo o de la asignación),
        con etiqueta 'label' ya formateada a prueba de vacíos.
        """
        ids_directos = (
            AuditoriaVisita.objects
            .filter(tecnico_id__isnull=False)
            .values_list("tecnico_id", flat=True)
            .distinct()
        )
        ids_asignaciones = (
            AuditoriaVisita.objects
            .filter(asignacion__asignado_a_id__isnull=False)
            .values_list("asignacion__asignado_a_id", flat=True)
            .distinct()
        )
        ids = set(ids_directos) | set(ids_asignaciones)
        users = Usuario.objects.filter(id__in=ids).order_by("first_name", "last_name", "id")
        data = [
            {"id": u.id, "label": self._display_name(u), "email": u.email}
            for u in users
        ]
        return Response(data)
