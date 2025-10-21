from django.utils import timezone
from django.conf import settings
from rest_framework import serializers

from .models import AuditoriaVisita, Tri, EstadoCliente
from asignaciones.models import HistorialAsignacion, DireccionAsignada

# Notificaciones (email)
from core.models import Notificacion
try:
    from core.notify import enviar_notificacion_real
except Exception:
    enviar_notificacion_real = None  # en dev si no existe, no rompe


def _normalize_block(val: str | None) -> str | None:
    if not val:
        return None
    v = str(val).strip()
    # Acepta "10-13", "10:00 a 13:00", etc.
    if v in ("10-13", "10:00 a 13:00", "10 a 13"):
        return "10-13"
    if v in ("14-18", "14:00 a 18:00", "14 a 18"):
        return "14-18"
    return None


def _status_to_canonical(raw: str | None) -> str | None:
    if raw is None:
        return None
    t = str(raw).strip().upper()
    # Soporta valores en minúscula que pueda mandar el front: "reagendo", etc.
    ali = {
        "AUTORIZA": "AUTORIZA",
        "SIN_MORADORES": "SIN_MORADORES",
        "RECHAZA": "RECHAZA",
        "CONTINGENCIA": "CONTINGENCIA",
        "MASIVO": "MASIVO",
        "REAGENDA": "REAGENDA",
        # sinónimos comunes
        "REAGENDO": "REAGENDA",
        "REAGENDA": "REAGENDA",
        "REAGENDÓ": "REAGENDA",
        "REAGENDADA": "REAGENDA",
        "REAGENDADO": "REAGENDA",
    }
    return ali.get(t) or ali.get(t.replace("Ó", "O"))


class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # Campos derivados desde la asignación (solo lectura)
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)
    tecnico_id = serializers.IntegerField(source="asignacion.asignado_a_id", read_only=True)

    # Salida cómoda de fotos (URLs)
    photos = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AuditoriaVisita
        fields = "__all__"  # exponemos todos los campos del modelo
        read_only_fields = (
            "id", "created_at", "tecnico",
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id", "photos",
        )

    def get_photos(self, obj: AuditoriaVisita):
        req = self.context.get("request")
        urls = []
        for f in (obj.photo1, obj.photo2, obj.photo3):
            if f:
                try:
                    url = f.url
                    if req is not None:
                        url = req.build_absolute_uri(url)
                    urls.append(url)
                except Exception:
                    pass
        return urls

    def validate(self, attrs):
        # normalizamos customer_status si viene en minúsculas
        raw_status = attrs.get("customer_status", None)
        if raw_status is not None:
            canon = _status_to_canonical(raw_status)
            if canon is None:
                raise serializers.ValidationError({"customer_status": "Valor inválido."})
            attrs["customer_status"] = canon
        else:
            # si no viene en payload, usamos el de la instancia (update)
            inst_status = getattr(self.instance, "customer_status", None)
            if inst_status:
                attrs["customer_status"] = _status_to_canonical(inst_status)

        # Si es REAGENDA, exigir fecha y bloque válidos (no pasados)
        if attrs.get("customer_status") == "REAGENDA":
            f = attrs.get("reschedule_date") or getattr(self.instance, "reschedule_date", None)
            b = attrs.get("reschedule_block") or getattr(self.instance, "reschedule_block", None)
            if not f or not b:
                raise serializers.ValidationError("Debe indicar fecha y bloque de reagendamiento.")
            if f < timezone.localdate():
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
            if _normalize_block(b) is None:
                raise serializers.ValidationError("Bloque inválido (use 10-13 o 14-18).")
            attrs["reschedule_block"] = _normalize_block(b)

        return attrs

    def create(self, validated_data):
        """
        Reglas clave:
        - Si customer_status == REAGENDA:
            * Actualiza asignacion.reagendado_fecha / reagendado_bloque (NO toca asignacion.fecha)
            * Mantiene estado actual; si estaba PENDIENTE la deja ASIGNADA
            * HistorialAsignacion: REAGENDADA (detalles con fecha/bloque)
            * (opcional) Registrar en tabla Reagendamiento si existe
            * Notificación EMAIL al técnico asignado (si hay email y SMTP)
        - Setea 'tecnico' con el usuario técnico que crea (si corresponde)
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # si el usuario es técnico, se autoasigna como 'tecnico' de la auditoría
        if user and getattr(user, "rol", None) == "tecnico":
            validated_data["tecnico"] = user

        audit: AuditoriaVisita = super().create(validated_data)

        try:
            asignacion: DireccionAsignada = audit.asignacion
        except Exception:
            asignacion = None

        # --- Reglas post-create
        if asignacion:
            status = audit.customer_status

            if status == "REAGENDA":
                f = audit.reschedule_date
                b = _normalize_block(audit.reschedule_block)

                # Mantener estado; si estaba PENDIENTE, marcar ASIGNADA
                new_estado = asignacion.estado
                if new_estado == "PENDIENTE":
                    new_estado = "ASIGNADA"

                old_fecha = asignacion.reagendado_fecha
                old_bloque = asignacion.reagendado_bloque

                asignacion.reagendado_fecha = f
                asignacion.reagendado_bloque = b
                asignacion.estado = new_estado
                asignacion.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado", "updated_at"])

                # Historial: REAGENDADA
                HistorialAsignacion.objects.create(
                    asignacion=asignacion,
                    accion=HistorialAsignacion.Accion.REAGENDADA,
                    detalles=f"Reagendada desde auditoría a {f} {b}",
                    usuario=user,
                )

                # (opcional) Registrar en Reagendamiento si el modelo existe
                try:
                    from asignaciones.models import Reagendamiento
                    Reagendamiento.objects.create(
                        asignacion=asignacion,
                        fecha_anterior=old_fecha,
                        bloque_anterior=old_bloque,
                        fecha_nueva=f,
                        bloque_nuevo=b,
                        usuario=user,
                    )
                except Exception:
                    pass

                # Notificación por email al técnico
                dest = getattr(asignacion.asignado_a, "email", "") or ""
                notif = Notificacion.objects.create(
                    tipo="reagendo",
                    asignacion=asignacion,
                    canal=Notificacion.Canal.EMAIL if dest else Notificacion.Canal.NONE,
                    destino=dest,
                    provider="",
                    payload={
                        "asignacion_id": asignacion.id,
                        "direccion": asignacion.direccion,
                        "comuna": asignacion.comuna,
                        "reagendado_fecha": str(f),
                        "reagendado_bloque": b,
                        "tecnico_id": getattr(user, "id", None),
                        "tecnico_email": dest,
                    },
                    status=Notificacion.Estado.QUEUED,
                )
                if dest and enviar_notificacion_real:
                    try:
                        enviar_notificacion_real(notif)
                    except Exception:
                        # si falla el envío real, dejamos la notificación en cola
                        pass

            elif status == "AUTORIZA":
                # Solo trazamos; NO tocamos estado de la asignación aquí
                HistorialAsignacion.objects.create(
                    asignacion=asignacion,
                    accion=HistorialAsignacion.Accion.CERRADA,
                    detalles="Auditoría: estado cliente 'Autoriza'.",
                    usuario=user,
                )
            else:
                # Otros estados -> traza genérica
                HistorialAsignacion.objects.create(
                    asignacion=asignacion,
                    accion=HistorialAsignacion.Accion.ESTADO_CLIENTE,
                    detalles=f"Auditoría: estado cliente = {status}.",
                    usuario=user,
                )

        return audit
