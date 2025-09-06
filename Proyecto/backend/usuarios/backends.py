from django.contrib.auth.backends import ModelBackend
from .models import Usuario

class EmailOrLocalBackend(ModelBackend):
    """
    Permite login con email o con la parte antes de @ (local-part)
    en el form de sesión (/api-auth/login/) y en admin si lo usas.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # Si es email
        if '@' in username:
            try:
                user = Usuario.objects.get(email__iexact=username)
            except Usuario.DoesNotExist:
                return None
        else:
            # Es local-part
            qs = Usuario.objects.filter(email__istartswith=f"{username}@")
            if qs.count() != 1:
                return None
            user = qs.first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None