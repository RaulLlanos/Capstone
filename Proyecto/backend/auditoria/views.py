# auditoria/views.py
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import AuditoriaVisita
from .serializers import AuditoriaVisitaSerializer


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
      - asignacion (id) / asignacion__asignado_a (id técnico asignado a la visita)
      - tecnico (id) / tecnico_id (compat)
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

    # Incluimos claves estándar y compatibilidad con *_id
    filterset_fields = {
        "customer_status": ["exact", "in"],
        "asignacion": ["exact"],                  # ?asignacion=7
        "asignacion__asignado_a": ["exact"],      # ?asignacion__asignado_a=29
        "tecnico": ["exact"],                     # ?tecnico=29
        "tecnico_id": ["exact"],                  # ?tecnico_id=29 (compat)
        "asignacion__comuna": ["exact"],
        "asignacion__zona": ["exact"],
        "created_at": ["gte", "lte"],
    }
    search_fields = ["asignacion__direccion", "asignacion__rut_cliente", "asignacion__comuna"]
    ordering_fields = ["created_at", "asignacion__comuna", "asignacion__zona"]

    def get_queryset(self):
        u = self.request.user
        rol = getattr(u, "rol", None)

        qs = self.queryset

        # Alcance por rol
        if rol == "tecnico":
            qs = qs.filter(
                Q(tecnico_id=u.id) |
                Q(asignacion__asignado_a_id=u.id)
            )

        # --- Compatibilidad explícita con parámetros usados por el Front ---
        # Aun teniendo DjangoFilterBackend, aplicamos estos filtros manuales
        # para asegurar que ?asignacion=<id>&tecnico_id=<id> siempre funcionen.
        asignacion_id = self.request.query_params.get("asignacion")
        if asignacion_id:
            qs = qs.filter(asignacion_id=asignacion_id)

        tecnico_id = self.request.query_params.get("tecnico_id")
        if tecnico_id:
            qs = qs.filter(tecnico_id=tecnico_id)

        return qs

    # Endpoint ADITIVO (no rompe APIs): lista de técnicos con nombre/email para combos
    @action(detail=False, methods=["get"], url_path="tecnicos")
    def tecnicos(self, request):
        base = self.get_queryset().select_related("tecnico")
        vals = (base.values(
            "tecnico_id",
            "tecnico__first_name",
            "tecnico__last_name",
            "tecnico__email",
        ).distinct())
        data = []
        for v in vals:
            tid = v["tecnico_id"]
            if not tid:
                continue
            nombre = f"{(v['tecnico__first_name'] or '').strip()} {(v['tecnico__last_name'] or '').strip()}".strip()
            label = nombre or (v["tecnico__email"] or f"Tec #{tid}")
            data.append({"id": tid, "nombre": label, "email": v["tecnico__email"] or ""})
        data.sort(key=lambda x: x["nombre"].lower())
        return Response(data)
