# asignaciones/serializers_actions.py
from rest_framework import serializers

class AsignarmeActionSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=False, default=True)

class EstadoClienteActionSerializer(serializers.Serializer):
    """
    Etapa 1 del Q5 (no pide fecha/bloque aquí).
    """
    estado_cliente = serializers.ChoiceField(choices=[
        ("autoriza", "Autoriza a ingresar"),
        ("sin_moradores", "Sin Moradores"),
        ("rechaza", "Rechaza"),
        ("contingencia", "Contingencia externa"),
        ("masivo", "Incidencia Masivo ClaroVTR"),
        ("reagendo", "Reagendó"),
    ])

class ReagendarActionSerializer(serializers.Serializer):
    """
    Etapa 2 del Q5 (solo cuando se eligió 'reagendo').
    """
    reagendado_fecha = serializers.DateField(help_text="YYYY-MM-DD (futura)")
    reagendado_bloque = serializers.ChoiceField(
        choices=[("10-13", "10:00 a 13:00"), ("14-18", "14:00 a 18:00")]
    )
