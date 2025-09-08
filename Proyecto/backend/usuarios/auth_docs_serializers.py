# usuarios/auth_docs_serializers.py
from rest_framework import serializers

class RegisterDocSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    rut_usuario = serializers.CharField(required=False, allow_blank=True)
    rol = serializers.ChoiceField(choices=['tecnico', 'auditor', 'admin'])

class LoginDocSerializer(serializers.Serializer):
    # Permitimos tres variantes como describiste
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)  # local-part antes del @
    login = serializers.CharField(required=False)     # email o local-part
    password = serializers.CharField()

class MeDocSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    rol = serializers.CharField()
