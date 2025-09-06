# usuarios/auth_views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from .auth_serializers import RegisterSerializer
from .models import Usuario

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

class LoginSerializer(TokenObtainPairSerializer):
    """
    Acepta:
    - {"email": "...", "password": "..."}
    - {"username": "localpart", "password": "..."}  # parte antes del @
    - {"login": "...", "password": "..."}           # email o localpart
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tu USERNAME_FIELD es 'email'; lo marcamos como no requerido para que
        # DRF no falle antes de tiempo cuando no venga en el payload.
        self.fields[self.username_field].required = False

    def validate(self, attrs):
        # Toma credenciales desde el cuerpo original (no de attrs)
        data = self.initial_data or {}
        login = data.get('email') or data.get('username') or data.get('login')
        password = data.get('password')

        if not login or not password:
            raise AuthenticationFailed('Faltan credenciales.')

        # Si mandan "jorge" (local-part), resolvemos el email real.
        if '@' not in login:
            qs = Usuario.objects.filter(email__istartswith=f"{login}@")
            if qs.count() != 1:
                raise AuthenticationFailed('Usuario ambiguo o inexistente. Usa el email completo.')
            login = qs.first().email

        # Inyecta el email en attrs para que el serializer base continúe
        attrs[self.username_field] = login
        attrs['password'] = password
        return super().validate(attrs)

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

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
