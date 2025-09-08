# usuarios/auth_views.py
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from .auth_serializers import RegisterSerializer
from .models import Usuario
from .auth_docs_serializers import RegisterDocSerializer, LoginDocSerializer, MeDocSerializer  # <—

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

# ---------- Registro ----------
@extend_schema(
    summary="Registro de usuario",
    request=RegisterDocSerializer,
    responses={
        201: MeDocSerializer,
        400: OpenApiResponse(description="Datos inválidos"),
    },
    examples=[
        OpenApiExample(
            "Ejemplo registro técnico",
            value={
                "email": "tecnico@acme.cl",
                "password": "Secreta123!",
                "first_name": "Jorge",
                "last_name": "López",
                "rut_usuario": "12.345.678-9",
                "rol": "tecnico"
            }
        )
    ]
)
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
@extend_schema(
    summary="Login (cookies HttpOnly)",
    description=(
        "Acepta 3 formatos:\n"
        "- {\"email\":\"...\",\"password\":\"...\"}\n"
        "- {\"username\":\"localpart\",\"password\":\"...\"}  # parte antes del @\n"
        "- {\"login\":\"...\",\"password\":\"...\"}           # email o local-part\n\n"
        "Guarda cookies `access` y `refresh`."
    ),
    request=LoginDocSerializer,
    responses={
        200: MeDocSerializer,
        401: OpenApiResponse(description="Credenciales inválidas"),
    },
    examples=[
        OpenApiExample("Login con email", value={"email": "tecnico@acme.cl", "password": "Secreta123!"}),
        OpenApiExample("Login con local-part", value={"username": "tecnico", "password": "Secreta123!"}),
        OpenApiExample("Login genérico", value={"login": "tecnico@acme.cl", "password": "Secreta123!"}),
    ]
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        login = (data.get('email') or data.get('username') or data.get('login') or '').strip()
        password = data.get('password') or ''
        if not login or not password:
            raise AuthenticationFailed('Faltan credenciales.')

        if '@' not in login:
            qs = Usuario.objects.filter(email__istartswith=f"{login}@")
            if qs.count() != 1:
                raise AuthenticationFailed('Usuario ambiguo o inexistente. Usa el email completo.')
            login = qs.first().email

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

# ---------- Refresh ----------
@extend_schema(
    summary="Refresh (renueva access desde refresh cookie)",
    responses={
        200: OpenApiResponse(description="Access renovado"),
        401: OpenApiResponse(description="Falta o es inválido el refresh"),
    }
)
class RefreshCookieView(APIView):
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

# ---------- Logout ----------
@extend_schema(
    summary="Logout (limpia cookies)",
    responses={204: OpenApiResponse(description="Sin contenido")}
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        resp = Response(status=204)
        _delete_cookie(resp, getattr(settings, 'JWT_AUTH_COOKIE', 'access'))
        _delete_cookie(resp, getattr(settings, 'JWT_AUTH_REFRESH_COOKIE', 'refresh'))
        return resp

# ---------- Me ----------
@extend_schema(
    summary="Perfil actual (por cookies)",
    responses={200: MeDocSerializer}
)
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
