# auditoria/migrations/0007_add_auditoria_fields.py
from django.db import migrations, models
import auditoria.models as auditoria_models


class Migration(migrations.Migration):

    dependencies = [
        ("auditoria", "0006_rename_fields_legibles"),
    ]

    operations = [
        # --- Renombres que confirmaste en makemigrations (respetamos esto) ---
        migrations.RenameField(
            model_name="auditoriavisita",
            old_name="reagendado_fecha",
            new_name="reschedule_date",
        ),
        migrations.RenameField(
            model_name="auditoriavisita",
            old_name="servicios",
            new_name="service_issues",
        ),

        # --- Campos legacy que se eliminan (según tu salida del makemigrations) ---
        migrations.RemoveField(model_name="auditoriavisita", name="bloque_agendamiento"),
        migrations.RemoveField(model_name="auditoriavisita", name="bloque_cierre"),
        migrations.RemoveField(model_name="auditoriavisita", name="bloque_config"),
        migrations.RemoveField(model_name="auditoriavisita", name="bloque_llegada"),
        migrations.RemoveField(model_name="auditoriavisita", name="bloque_proceso"),
        migrations.RemoveField(model_name="auditoriavisita", name="categorias"),
        migrations.RemoveField(model_name="auditoriavisita", name="descripcion_problema"),
        migrations.RemoveField(model_name="auditoriavisita", name="estado_cliente"),
        migrations.RemoveField(model_name="auditoriavisita", name="fotos"),
        migrations.RemoveField(model_name="auditoriavisita", name="percepcion"),
        migrations.RemoveField(model_name="auditoriavisita", name="reagendado_bloque"),

        # ----------------------------------------------------------------------
        # CAST SEGURO: boolean -> smallint para ont_modem_ok
        # (debe ir ANTES del AlterField de abajo)
        # ----------------------------------------------------------------------
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='auditoria_auditoriavisita'
                      AND column_name='ont_modem_ok'
                      AND data_type='boolean'
                ) THEN
                    -- dropeamos default por si estorba
                    ALTER TABLE auditoria_auditoriavisita
                      ALTER COLUMN ont_modem_ok DROP DEFAULT;

                    -- mapeo: TRUE->1 (Sí), FALSE->2 (No), NULL->3 (No Aplica)
                    ALTER TABLE auditoria_auditoriavisita
                      ALTER COLUMN ont_modem_ok TYPE smallint
                      USING CASE
                              WHEN ont_modem_ok IS TRUE  THEN 1
                              WHEN ont_modem_ok IS FALSE THEN 2
                              ELSE 3
                           END;
                END IF;
            END$$;
            """,
            reverse_sql="""
            ALTER TABLE auditoria_auditoriavisita
              ALTER COLUMN ont_modem_ok TYPE boolean
              USING CASE
                      WHEN ont_modem_ok = 1 THEN TRUE
                      WHEN ont_modem_ok = 2 THEN FALSE
                      ELSE NULL
                   END;
            """
        ),

        # --- Ajuste de tipo/defecto del campo ya casteado ---
        migrations.AlterField(
            model_name="auditoriavisita",
            name="ont_modem_ok",
            field=models.PositiveSmallIntegerField(default=3),
        ),

        # --- Nuevos campos alineados a tu models.py ---
        # Reagendamiento
        migrations.AddField(
            model_name="auditoriavisita",
            name="reschedule_slot",
            field=models.CharField(max_length=10, blank=True),
        ),

        # Estado del cliente (nuevo nombre)
        migrations.AddField(
            model_name="auditoriavisita",
            name="customer_status",
            field=models.CharField(max_length=20, blank=True),
        ),

        # Q8 checkboxes ya renombrado a service_issues (JSON list) -> ya existe por RenameField

        # Q9 Internet
        migrations.AddField(
            model_name="auditoriavisita",
            name="internet_issue_category",
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="internet_issue_other",
            field=models.CharField(max_length=200, blank=True),
        ),

        # Q10 TV
        migrations.AddField(
            model_name="auditoriavisita",
            name="tv_issue_category",
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="tv_issue_other",
            field=models.CharField(max_length=200, blank=True),
        ),

        # Q11 Otro
        migrations.AddField(
            model_name="auditoriavisita",
            name="other_issue_description",
            field=models.TextField(blank=True),
        ),

        # Fotos (Q13–Q15)
        migrations.AddField(
            model_name="auditoriavisita",
            name="photo1",
            field=models.ImageField(upload_to=auditoria_models._upload_auditoria, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="photo2",
            field=models.ImageField(upload_to=auditoria_models._upload_auditoria, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="photo3",
            field=models.ImageField(upload_to=auditoria_models._upload_auditoria, null=True, blank=True),
        ),

        # Q73 HFC
        migrations.AddField(
            model_name="auditoriavisita",
            name="hfc_problem_description",
            field=models.TextField(blank=True),
        ),

        # AGENDAMIENTO (Q16 + Q71)
        migrations.AddField(
            model_name="auditoriavisita",
            name="schedule_informed_datetime",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="schedule_informed_adult_required",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="schedule_informed_services",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="schedule_comments",
            field=models.TextField(blank=True),
        ),

        # Llegada (Q17/18)
        migrations.AddField(
            model_name="auditoriavisita",
            name="arrival_within_slot",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="identification_shown",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="explained_before_start",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="arrival_comments",
            field=models.TextField(blank=True),
        ),

        # Proceso instalación (Q19/20)
        migrations.AddField(
            model_name="auditoriavisita",
            name="asked_equipment_location",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="tidy_and_safe_install",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="tidy_cabling",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="verified_signal_levels",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="install_process_comments",
            field=models.TextField(blank=True),
        ),

        # Configuración/pruebas (Q21/22)
        migrations.AddField(
            model_name="auditoriavisita",
            name="configured_router",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="tested_device",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="tv_functioning",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="left_instructions",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="config_comments",
            field=models.TextField(blank=True),
        ),

        # Cierre (Q23/24)
        migrations.AddField(
            model_name="auditoriavisita",
            name="reviewed_with_client",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="got_consent_signature",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="left_contact_info",
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="closure_comments",
            field=models.TextField(blank=True),
        ),

        # Percepción/NPS (Q25–Q28)
        migrations.AddField(
            model_name="auditoriavisita",
            name="perception_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="nps_process",
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="nps_technician",
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="nps_brand",
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),

        # Solución / Gestión / Info
        migrations.AddField(
            model_name="auditoriavisita",
            name="resolution",
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="order_type",
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="info_type",
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="malpractice_company_detail",
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name="auditoriavisita",
            name="malpractice_installer_detail",
            field=models.CharField(max_length=200, blank=True),
        ),

        # Finalizar (Q12)
        migrations.AddField(
            model_name="auditoriavisita",
            name="final_problem_description",
            field=models.TextField(blank=True),
        ),

        # (Opcional) aseguramos el ordering del modelo
        migrations.AlterModelOptions(
            name="auditoriavisita",
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
