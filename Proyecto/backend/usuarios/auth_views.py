# backend/usuarios/auth_views.py
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .auth_serializers import RegisterSerializer

User = get_user_model()


# ===== helpers cookies =====

def _set_cookie(response, name, value, max_age=None):
    """
    Setea cookies HttpOnly para access/refresh con los flags desde settings.
    """
    samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "Lax")
    secure = bool(getattr(settings, "JWT_COOKIE_SECURE", False))
    domain = getattr(settings, "JWT_COOKIE_DOMAIN", None) or None
    path = getattr(settings, "JWT_COOKIE_PATH", "/")

    response.set_cookie(
        name,
        value,
        max_age=max_age,  # en segundos
        httponly=True,
        secure=secure,
        samesite=samesite,
        domain=domain,
        path=path,
    )
    return response


def _delete_cookie(response, name):
    domain = getattr(settings, "JWT_COOKIE_DOMAIN", None) or None
    path = getattr(settings, "JWT_COOKIE_PATH", "/")
    response.delete_cookie(name, domain=domain, path=path)
    return response


def _issue_tokens_for_user(user: User) -> dict:
    """
    Crea par (refresh, access) usando SimpleJWT.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ===== Vistas =====

class RegisterView(APIView):
    """
    Crea un usuario. Para el admin inicial usa el bootstrap (management command).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "rol": getattr(user, "rol", None),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # permitimos "login" (local-part o e-mail) o directamente "email"
        login_val = request.data.get("login") or request.data.get("email")
        password = request.data.get("password")

        if not login_val or not password:
            return Response(
                {"detail": "login/email y password son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Usa tu backend EmailOrLocalBackend
        user = authenticate(request, username=login_val, password=password)
        if not user:
            return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        # Emite tokens y setea cookies HttpOnly
        tokens = _issue_tokens_for_user(user)
        access_name = getattr(settings, "JWT_AUTH_COOKIE", "access")
        refresh_name = getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh")

        resp = Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "rol": getattr(user, "rol", None),
            },
            status=status.HTTP_200_OK,
        )
        # access ~ minutos, refresh ~ días (según settings SIMPLE_JWT)
        resp = _set_cookie(resp, access_name, tokens["access"])
        resp = _set_cookie(resp, refresh_name, tokens["refresh"])
        return resp


class RefreshCookieView(APIView):
    """
    Lee el refresh desde cookie y entrega un nuevo access (cookie).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_name = getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh")
        access_name = getattr(settings, "JWT_AUTH_COOKIE", "access")
        refresh_token = request.COOKIES.get(refresh_name)

        if not refresh_token:
            return Response({"detail": "No hay refresh en cookie."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)
        except Exception:
            return Response({"detail": "Refresh inválido o expirado."}, status=status.HTTP_401_UNAUTHORIZED)

        resp = Response({"detail": "Access renovado."}, status=status.HTTP_200_OK)
        resp = _set_cookie(resp, access_name, new_access)
        return resp


class LogoutView(APIView):
    """
    Borra cookies access y refresh. (Permite cerrar sesión aunque el access haya expirado).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        access_name = getattr(settings, "JWT_AUTH_COOKIE", "access")
        refresh_name = getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh")
        resp = Response({"detail": "Sesión finalizada."}, status=status.HTTP_200_OK)
        resp = _delete_cookie(resp, access_name)
        resp = _delete_cookie(resp, refresh_name)
        return resp


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "rol": getattr(user, "rol", None),
            },
            status=status.HTTP_200_OK,
        )


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # MUY IMPORTANTE: evita fallar por falta de auth

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        return Response({"detail": "CSRF cookie set"})
