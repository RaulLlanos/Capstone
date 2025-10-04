from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=8)
    rut = serializers.CharField(read_only=True)  # "XXXXXXXX-D" para mostrar

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "first_name", "last_name",
            "rol",
            "rut_num", "dv", "rut",
            "is_active", "is_staff", "date_joined",
            "password",
        ]
        read_only_fields = ["id", "date_joined", "is_staff"]

    def validate(self, attrs):
        dv = attrs.get("dv")
        if dv:
            attrs["dv"] = dv.upper()
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        is_admin = bool(request and getattr(request.user, "rol", None) == "administrador")

        if not is_admin:
            for sensitive in ("rol", "is_staff", "is_superuser"):
                validated_data.pop(sensitive, None)

        pwd = validated_data.pop("password", None)

        if "dv" in validated_data and validated_data["dv"]:
            validated_data["dv"] = validated_data["dv"].upper()

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if pwd:
            instance.set_password(pwd)

        instance.save()
        return instance
