# core/auth.py
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieOrHeaderJWTAuthentication(JWTAuthentication):
    """
    Intenta primero Authorization: Bearer.
    Si no viene, usa el JWT de la cookie (p.ej. 'access').
    """
    def authenticate(self, request):
        # 1) Header estándar
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        # 2) Cookie
        cookie_name = getattr(settings, "JWT_AUTH_COOKIE", "access")
        raw_token = request.COOKIES.get(cookie_name)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        return (self.get_user(validated_token), validated_token)
