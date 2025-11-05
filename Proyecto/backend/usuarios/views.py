from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import AdminAuditorFull_TechReadOnly
from .models import Usuario
from .serializers import UsuarioSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    - Administrador: CRUD total de usuarios.
    - Técnico: SOLO lectura de su propio usuario.
    """
    queryset = Usuario.objects.all().order_by("-date_joined")
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, AdminAuditorFull_TechReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "email", "first_name", "last_name"]
    filterset_fields = ["rol", "is_active", "is_staff"]

    def get_queryset(self):
        u = self.request.user
        if getattr(u, "rol", None) == "administrador":
            return super().get_queryset()
        return Usuario.objects.filter(id=u.id)

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    def update(self, request, *args, **kwargs):
        # Acepta PUT como PATCH para no exigir todos los campos
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
