# core/serializers.py
from rest_framework import serializers
from .models import Configuracion, LogSistema, Notificacion

class ConfiguracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuracion
        fields = ["id", "clave", "valor", "tipo", "descripcion", "created_at", "updated_at"]

    def validate_clave(self, v):
        if not v or v.strip() == "":
            raise serializers.ValidationError("La clave es obligatoria.")
        return v.strip()

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = "__all__"

class LogSistemaSerializer(serializers.ModelSerializer):
    usuario_email = serializers.SerializerMethodField()

    class Meta:
        model = LogSistema
        fields = ["id", "usuario", "usuario_email", "accion", "detalle", "created_at"]

    def get_usuario_email(self, obj):
        return getattr(obj.usuario, "email", None)
