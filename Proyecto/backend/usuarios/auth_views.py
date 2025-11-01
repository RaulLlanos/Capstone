from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

from .auth_serializers import RegisterSerializer  # Asegúrate que el archivo se llame auth_serializers.py
from .models import Usuario

def _set_cookie(response, name, value, max_age=None):
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        path=getattr(settings, "JWT_COOKIE_PATH", "/"),
        domain=getattr(settings, "JWT_COOKIE_DOMAIN", None),
        secure=getattr(settings, "JWT_COOKIE_SECURE", False),
        httponly=True,
        samesite=getattr(settings, "JWT_COOKIE_SAMESITE", "Lax"),
    )

def _delete_cookie(response, name):
    response.delete_cookie(
        name,
        path=getattr(settings, "JWT_COOKIE_PATH", "/"),
        domain=getattr(settings, "JWT_COOKIE_DOMAIN", None),
        samesite=getattr(settings, "JWT_COOKIE_SAMESITE", "Lax"),
    )

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"id": user.id, "email": user.email}, status=201)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        login = data.get("login") or data.get("email")
        password = data.get("password")

        if not login or not password:
            return Response({"detail": "Faltan credenciales."}, status=400)

        # Soporta login con email completo o local-part (antes de @) si no ambiguo
        user = None
        if "@" in login:
            user = authenticate(request, username=login, password=password)
        else:
            # local-part → busca único email que empiece con local-part
            qs = Usuario.objects.filter(email__istartswith=f"{login}@")
            if qs.count() == 1:
                user = authenticate(request, username=qs.first().email, password=password)
            else:
                # intenta igualmente authenticate (por si tu backend soporta local-part directo)
                user = authenticate(request, username=login, password=password)

        if user is None:
            raise AuthenticationFailed("Credenciales inválidas.")

        # Genera tokens y setea cookies HttpOnly
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        resp = Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "rol": user.rol,
        }, status=200)

        _set_cookie(resp, getattr(settings, "JWT_AUTH_COOKIE", "access"), str(access), max_age=15*60)
        _set_cookie(resp, getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh"), str(refresh), max_age=30*24*3600)
        return resp

class LogoutView(APIView):
    def post(self, request):
        resp = Response({"detail": "ok"})
        _delete_cookie(resp, getattr(settings, "JWT_AUTH_COOKIE", "access"))
        _delete_cookie(resp, getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh"))
        return resp

class MeView(APIView):
    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "rol": u.rol,
        })
