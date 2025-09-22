from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    # Forzamos password requerido y mínimo 8, y lo validamos con los validadores de Django
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        allow_blank=False,
    )
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
        # Normaliza DV en mayúsculas (k → K)
        dv = attrs.get("dv")
        if dv:
            attrs["dv"] = dv.upper()

        # Validación amistosa de RUT duplicado (además del constraint de BD)
        rut_num = attrs.get("rut_num")
        dv_val = attrs.get("dv")
        if rut_num is not None and dv_val:
            qs = Usuario.objects.filter(rut_num=rut_num, dv=dv_val.upper())
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"rut_num": "Ya existe un usuario con este RUT."}
                )

        return attrs

    def create(self, validated_data):
        # Password es requerido por el serializer, aquí lo validamos con Django
        password = validated_data.pop("password")

        # Ejecuta los validadores configurados en settings (MinimumLength, etc.)
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        user = Usuario(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get("request")
        is_auditor = bool(request and getattr(request.user, "rol", None) == "auditor")

        # Solo auditor puede cambiar rol / staff / superuser vía API
        if not is_auditor:
            for sensitive in ("rol", "is_staff", "is_superuser"):
                validated_data.pop(sensitive, None)

        pwd = validated_data.pop("password", None)

        # Normaliza DV si viene
        if "dv" in validated_data and validated_data["dv"]:
            validated_data["dv"] = validated_data["dv"].upper()

        for k, v in validated_data.items():
            setattr(instance, k, v)

        # Si viene password, lo validamos y actualizamos
        if pwd:
            try:
                validate_password(pwd, user=instance)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)})
            instance.set_password(pwd)

        instance.save()
        return instance
