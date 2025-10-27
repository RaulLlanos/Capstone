# usuarios/auth_views.py
from django.conf import settings
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from core.models import LogSistema
from .auth_serializers import RegisterSerializer
from .models import Usuario


# ==========================
# Helpers
# ==========================
def _set_cookie(response, name, value, max_age_seconds: int):
    response.set_cookie(
        key=name,
        value=value,
        max_age=int(max_age_seconds),
        httponly=True,
        samesite=getattr(settings, "JWT_COOKIE_SAMESITE", "Lax"),
        secure=getattr(settings, "JWT_COOKIE_SECURE", False),
        path=getattr(settings, "JWT_COOKIE_PATH", "/"),
        domain=getattr(settings, "JWT_COOKIE_DOMAIN", None),
    )


def _delete_cookie(response, name: str):
    response.delete_cookie(
        key=name,
        path=getattr(settings, "JWT_COOKIE_PATH", "/"),
        domain=getattr(settings, "JWT_COOKIE_DOMAIN", None),
        samesite=getattr(settings, "JWT_COOKIE_SAMESITE", "Lax"),
    )


def _client_info(request):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", "")
    ua = request.META.get("HTTP_USER_AGENT", "")
    return ip, ua


def _log(accion, detalle, usuario=None):
    LogSistema.objects.create(
        usuario=usuario,
        accion=getattr(LogSistema.Accion, accion, accion),
        detalle=detalle,
    )


# ==========================
# Vistas
# ==========================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()

        # (Opcional) registra el alta por este flujo público
        _log(
            "USER_SELF_REGISTER",
            f"Alta de usuario {user.email} ({timezone.now().isoformat()})",
            usuario=None,
        )

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "rol": user.rol,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/token/
    - Setea cookies HttpOnly (access/refresh).
    - (Opcional) Si settings.JWT_LOGIN_RETURN_TOKENS=True, también devuelve access/refresh en el body.
    - Registra LOGIN_SUCCESS / LOGIN_FAIL en LogSistema.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        login = (data.get("email") or data.get("username") or data.get("login") or "").strip()
        password = data.get("password") or ""

        ip, ua = _client_info(request)

        if not login or not password:
            _log("LOGIN_FAIL", f"Faltan credenciales para login={login} ip={ip} ua={ua}", usuario=None)
            return Response({"detail": "Faltan credenciales."}, status=status.HTTP_401_UNAUTHORIZED)

        # Permites login con 'usuario' sin dominio → intenta resolver a email completo
        if "@" not in login:
            qs = Usuario.objects.filter(email__istartswith=f"{login}@")
            if qs.count() != 1:
                _log("LOGIN_FAIL", f"Ambiguo/inexistente login={login} ip={ip} ua={ua}", usuario=None)
                return Response({"detail": "Usuario ambiguo o inexistente. Usa el email completo."},
                                status=status.HTTP_401_UNAUTHORIZED)
            login = qs.first().email

        user = authenticate(request, username=login, password=password)
        if not user or not user.is_active:
            _log("LOGIN_FAIL", f"Credenciales inválidas para {login} ip={ip} ua={ua}", usuario=None)
            return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        # Genera tokens (SimpleJWT)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        access_s = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
        refresh_s = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())

        user_payload = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "rol": getattr(user, "rol", None),
        }

        # Body por defecto: solo info de usuario (tokens opcionales)
        resp = Response({"user": user_payload})

        # Si quieres tokens en body (para Bearer en front/QA), habilita el flag en settings/.env
        if getattr(settings, "JWT_LOGIN_RETURN_TOKENS", False):
            resp.data.update({"access": str(access), "refresh": str(refresh)})

        # Setea cookies (flujo web)
        _set_cookie(resp, getattr(settings, "JWT_AUTH_COOKIE", "access"), str(access), access_s)
        _set_cookie(resp, getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh"), str(refresh), refresh_s)

        _log("LOGIN_SUCCESS", f"Login OK {user.email} ip={ip} ua={ua}", usuario=user)
        return resp


class RefreshCookieView(APIView):
    """
    POST /auth/refresh
    - Lee refresh desde cookie y renueva access (cookie + opcional body).
    - Registra TOKEN_REFRESH / TOKEN_REFRESH_FAIL.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie_name = getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh")
        raw_refresh = request.COOKIES.get(refresh_cookie_name)

        ip, ua = _client_info(request)

        if not raw_refresh:
            _log("TOKEN_REFRESH_FAIL", f"Sin refresh cookie ip={ip} ua={ua}", usuario=None)
            return Response({"detail": "Falta refresh cookie."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(raw_refresh)
            access = refresh.access_token

            # intenta recuperar usuario para el log (no es crítico)
            user = None
            uid = refresh.get("user_id", None)
            if uid:
                user = Usuario.objects.filter(id=uid).first()

        except TokenError:
            _log("TOKEN_REFRESH_FAIL", f"Refresh inválido/expirado ip={ip} ua={ua}", usuario=None)
            return Response({"detail": "Refresh inválido/expirado."}, status=status.HTTP_401_UNAUTHORIZED)

        access_s = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())

        # Por coherencia: siempre devolvemos un pequeño mensaje + access (útil para QA);
        # si no quieres el access en body, puedes ocultarlo con otro flag.
        resp = Response({"detail": "Access renovado.", "access": str(access)})

        _set_cookie(resp, getattr(settings, "JWT_AUTH_COOKIE", "access"), str(access), access_s)

        _log("TOKEN_REFRESH", f"Refresh OK ip={ip} ua={ua}", usuario=user)
        return resp


class LogoutView(APIView):
    """
    POST /auth/logout
    - Borra cookies JWT.
    - Registra LOGOUT.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ip, ua = _client_info(request)
        user = request.user

        resp = Response(status=status.HTTP_204_NO_CONTENT)
        _delete_cookie(resp, getattr(settings, "JWT_AUTH_COOKIE", "access"))
        _delete_cookie(resp, getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "refresh"))

        _log("LOGOUT", f"Logout {user.email} ip={ip} ua={ua}", usuario=user)
        return resp


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response(
            {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "rol": u.rol,
            }
        )


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({"csrftoken": token})
