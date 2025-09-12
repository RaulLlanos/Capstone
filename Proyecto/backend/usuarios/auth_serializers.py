from rest_framework import serializers
from .models import Usuario

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ("email", "password", "first_name", "last_name", "rut_num", "dv", "rol")

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("El correo ya está registrado.")
        return value

    def validate(self, attrs):
        dv = attrs.get("dv")
        if dv:
            attrs["dv"] = dv.upper()
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Usuario(**validated_data)
        user.set_password(password)  # se hashea según PASSWORD_HASHERS
        user.save()
        return user
