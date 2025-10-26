# core/middleware.py
from django.http import JsonResponse
from django.conf import settings

# Intentamos resolver el usuario también con JWT antes de DRF
try:
    from usuarios.auth_cookie import CookieJWTAuthentication
except Exception:  # fallback si no existe por cualquier motivo
    CookieJWTAuthentication = None

try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
except Exception:
    JWTAuthentication = None

# Logs (opcional si la app aún no migró LogSistema)
try:
    from core.models import LogSistema
except Exception:
    LogSistema = None

ROLE_ROUTE_RULES = getattr(settings, "ROLE_ROUTE_RULES", {})

class RoleAuthorizationMiddleware:
    """
    Autorización por prefijo de URL y rol.
    - Lee settings.ROLE_ROUTE_RULES, ej:
        {
            "/api/admin/": {"administrador"},
            "/api/asignaciones/": {"administrador","tecnico"},
        }
    - Intenta autenticar al usuario ANTES de DRF:
        * Si request.user ya está autenticado (session), úsalo.
        * Si no, intenta JWT desde cookie o header (Bearer ...).
        * Si no logra autenticación aquí, contesta 401 en rutas protegidas.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._jwt_auth = JWTAuthentication() if JWTAuthentication else None
        self._cookie_jwt_auth = CookieJWTAuthentication() if CookieJWTAuthentication else None

    def _maybe_authenticate_jwt(self, request):
        """
        Intenta autenticar con cookie-JWT y luego con Authorization: Bearer.
        No levanta excepción (best-effort).
        """
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return user

        # Cookie JWT (si está disponible)
        if self._cookie_jwt_auth:
            try:
                res = self._cookie_jwt_auth.authenticate(request)
                if res:
                    return res[0]  # (user, token)
            except Exception:
                pass

        # Header Authorization: Bearer ...
        if self._jwt_auth:
            try:
                res = self._jwt_auth.authenticate(request)
                if res:
                    return res[0]
            except Exception:
                pass

        return None

    def __call__(self, request):
        path = (request.path or "/")
        norm = path if path.endswith("/") else (path + "/")

        # Reglas por prefijo
        for prefix, allowed_roles in ROLE_ROUTE_RULES.items():
            if norm.startswith(prefix):
                # Obtén (o resuelve) usuario
                user = self._maybe_authenticate_jwt(request)
                if user and not getattr(request, "user", None):
                    # por si acaso; normalmente AuthenticationMiddleware ya setea user
                    request.user = user
                elif user and not getattr(request.user, "is_authenticated", False):
                    # si estaba AnonymousUser, sobrescribimos
                    request.user = user

                if not user or not getattr(user, "is_authenticated", False):
                    # Log 401 (solo si tenemos LogSistema)
                    if LogSistema:
                        try:
                            LogSistema.objects.create(
                                usuario=None,
                                accion=getattr(LogSistema.Accion, "AUTHZ_DENY", "AUTHZ_DENY"),
                                detalle=f"401 en {norm}: no autenticado",
                            )
                        except Exception:
                            pass
                    return JsonResponse({"detail": "Authentication required"}, status=401)

                rol = getattr(user, "rol", None)
                if rol not in allowed_roles:
                    # Log 403 (solo si tenemos LogSistema)
                    if LogSistema:
                        try:
                            LogSistema.objects.create(
                                usuario=user,
                                accion=getattr(LogSistema.Accion, "AUTHZ_FORBIDDEN", "AUTHZ_FORBIDDEN"),
                                detalle=f"403 en {norm}: rol '{rol}' no permitido (permitidos={sorted(list(allowed_roles))})",
                            )
                        except Exception:
                            pass
                    return JsonResponse({"detail": "Forbidden"}, status=403)

                break  # ya aplicó una regla de prefijo

        return self.get_response(request)
