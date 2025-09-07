# usuarios/auth_views.py
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .auth_serializers import RegisterSerializer
from .models import Usuario

# ---------- Helpers para cookies ----------
def _set_cookie(response, name, value, max_age_seconds: int):
    response.set_cookie(
        key=name,
        value=value,
        max_age=int(max_age_seconds),
        httponly=True,
        samesite=getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax'),
        secure=getattr(settings, 'JWT_COOKIE_SECURE', False),
        path=getattr(settings, 'JWT_COOKIE_PATH', '/'),
        domain=getattr(settings, 'JWT_COOKIE_DOMAIN', None),
    )

def _delete_cookie(response, name: str):
    response.delete_cookie(
        key=name,
        path=getattr(settings, 'JWT_COOKIE_PATH', '/'),
        domain=getattr(settings, 'JWT_COOKIE_DOMAIN', None),
        samesite=getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax'),
    )

# ---------- Registro (igual al tuyo) ----------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'rol': user.rol,
        }, status=status.HTTP_201_CREATED)

# ---------- Login con cookies HttpOnly ----------
class LoginView(APIView):
    """
    Acepta:
    - {"email": "...", "password": "..."}
    - {"username": "localpart", "password": "..."}  # parte antes del @
    - {"login": "...", "password": "..."}           # email o localpart
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        login = (data.get('email') or data.get('username') or data.get('login') or '').strip()
        password = data.get('password') or ''
        if not login or not password:
            raise AuthenticationFailed('Faltan credenciales.')

        # Si mandan local-part (“jorge”), resolvemos email único
        if '@' not in login:
            qs = Usuario.objects.filter(email__istartswith=f"{login}@")
            if qs.count() != 1:
                raise AuthenticationFailed('Usuario ambiguo o inexistente. Usa el email completo.')
            login = qs.first().email

        # Tu backend EmailOrLocalBackend soporta email/local-part
        user = authenticate(request, username=login, password=password)
        if not user or not user.is_active:
            return Response({'detail': 'Credenciales inválidas.'}, status=401)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        access_s  = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        refresh_s = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

        resp = Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'rol': getattr(user, 'rol', None),
        })

        _set_cookie(resp, getattr(settings, 'JWT_AUTH_COOKIE', 'access'),  str(access),  access_s)
        _set_cookie(resp, getattr(settings, 'JWT_AUTH_REFRESH_COOKIE', 'refresh'), str(refresh), refresh_s)
        return resp

# ---------- Refresh de access leyendo refresh cookie ----------
class RefreshCookieView(APIView):
    """Renueva el access leyendo el refresh desde cookie HttpOnly."""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie_name = getattr(settings, 'JWT_AUTH_REFRESH_COOKIE', 'refresh')
        raw_refresh = request.COOKIES.get(refresh_cookie_name)
        if not raw_refresh:
            return Response({'detail': 'Falta refresh cookie.'}, status=401)

        try:
            refresh = RefreshToken(raw_refresh)
            access = refresh.access_token
        except TokenError:
            return Response({'detail': 'Refresh inválido/expirado.'}, status=401)

        access_s = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
        resp = Response({'detail': 'Access renovado.'})
        _set_cookie(resp, getattr(settings, 'JWT_AUTH_COOKIE', 'access'), str(access), access_s)
        return resp

# ---------- Logout: borra cookies ----------
class LogoutView(APIView):
    """Cierra sesión: borra cookies de access y refresh."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        resp = Response(status=204)
        _delete_cookie(resp, getattr(settings, 'JWT_AUTH_COOKIE', 'access'))
        _delete_cookie(resp, getattr(settings, 'JWT_AUTH_REFRESH_COOKIE', 'refresh'))
        return resp

# ---------- Me (igual al tuyo) ----------
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "rol": u.rol,
        })
