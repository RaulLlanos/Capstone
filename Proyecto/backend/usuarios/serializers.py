# usuarios/serializers.py
from rest_framework import serializers

# Import a prueba de balas si 'UsuarioSistema' no existe aún
try:
    from .models import Usuario, UsuarioSistema
except Exception:  # pragma: no cover
    from .models import Usuario
    UsuarioSistema = None  # type: ignore

# Longitud mínima de pass dinámica desde Configuracion (fallback 8)
try:
    from core.models import Configuracion
    def _min_pass_len():
        return max(1, Configuracion.get_int("MIN_PASS_LENGTH", 8))
except Exception:  # pragma: no cover
    def _min_pass_len():
        return 8


def _full_name_or_fallback(obj) -> str:
    """
    'Nombre Apellido' -> si vacío, local-part del email -> si vacío, 'Tec#ID'
    """
    fn = (getattr(obj, "first_name", "") or "").strip()
    ln = (getattr(obj, "last_name", "") or "").strip()
    full = f"{fn} {ln}".strip()
    if full:
        return full
    email = (getattr(obj, "email", "") or "").strip()
    if email:
        local = email.split("@")[0]
        if local:
            return local
    uid = getattr(obj, "id", None)
    return f"Tec#{uid}" if uid else ""


# ---------- (opcional) lista desde UsuarioSistema ----------
if UsuarioSistema is not None:
    class UsuarioSistemaListSerializer(serializers.ModelSerializer):
        nombre = serializers.SerializerMethodField()
        full_name = serializers.SerializerMethodField()

        class Meta:
            model = UsuarioSistema
            fields = [
                "id", "first_name", "last_name", "nombre", "full_name",
                "email", "rol", "is_active", "date_joined",
            ]

        def get_nombre(self, obj):
            return _full_name_or_fallback(obj)

        def get_full_name(self, obj):
            return _full_name_or_fallback(obj)
else:
    # Stub inofensivo si no existe el modelo
    class UsuarioSistemaListSerializer(serializers.Serializer):  # type: ignore
        pass


# ---------- lista desde Usuario (fallback general) ----------
class UsuarioListSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id", "first_name", "last_name", "nombre", "full_name",
            "email", "rol", "is_active", "date_joined",
        ]

    def get_nombre(self, obj):
        return _full_name_or_fallback(obj)

    def get_full_name(self, obj):
        return _full_name_or_fallback(obj)


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=1)
    rut = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)  # ← NUEVO

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "first_name", "last_name",
            "rol",
            "rut_num", "dv", "rut",
            "is_active", "is_staff", "date_joined",
            "password",
            "full_name",  # ← NUEVO, para combos del FE
        ]
        read_only_fields = ["id", "date_joined", "is_staff", "rut", "full_name"]

    # === Reglas de negocio ===
    def validate_email(self, value):
        # Evita duplicados (case-insensitive) y excluye el propio registro en update
        qs = Usuario.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("El correo ya está registrado.")
        return value

    def validate_password(self, value):
        if value is None:
            return value
        min_len = _min_pass_len()
        if len(value) < min_len:
            raise serializers.ValidationError(f"La contraseña debe tener al menos {min_len} caracteres.")
        return value

    def validate(self, attrs):
        dv = attrs.get("dv")
        if dv:
            attrs["dv"] = dv.upper()
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        # Si envían password, valida longitud mínima dinámica
        if password is not None:
            self.validate_password(password)
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
        if pwd is not None:
            self.validate_password(pwd)

        if "dv" in validated_data and validated_data["dv"]:
            validated_data["dv"] = validated_data["dv"].upper()

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if pwd:
            instance.set_password(pwd)

        instance.save()
        return instance

    def get_full_name(self, obj):
        return _full_name_or_fallback(obj)


# === Pequeño serializer para PUT /admin/usuarios/:id/rol ===
class UsuarioRoleUpdateSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=[("administrador", "Administrador"), ("tecnico", "Técnico")])
