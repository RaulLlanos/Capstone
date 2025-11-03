# asignaciones/migrations/0006_centro_a_oriente.py
from django.db import migrations

def centro_a_oriente(apps, schema_editor):
    DireccionAsignada = apps.get_model("asignaciones", "DireccionAsignada")
    DireccionAsignada.objects.filter(zona="CENTRO").update(zona="ORIENTE")

class Migration(migrations.Migration):
    dependencies = [
        ("asignaciones", "0005_remove_direccionasignada_uniq_activa_por_cliente_vivienda_and_more"),  # ← PON AQUÍ TU MIGRACIÓN ANTERIOR REAL (sin .py)
    ]
    operations = [
        migrations.RunPython(centro_a_oriente, migrations.RunPython.noop),
    ]
