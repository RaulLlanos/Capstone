# usuarios/auth_cookie.py
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    Auth que primero intenta leer el access token desde una cookie HttpOnly
    (settings.JWT_AUTH_COOKIE). Si no está, cae al header Authorization.
    """
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            cookie_name = getattr(settings, 'JWT_AUTH_COOKIE', 'access')
            raw_token = request.COOKIES.get(cookie_name)
            if not raw_token:
                return None
            validated = self.get_validated_token(raw_token)
            return self.get_user(validated), validated

        return super().authenticate(request)
