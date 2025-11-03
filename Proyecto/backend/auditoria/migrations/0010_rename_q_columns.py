# auditoria/migrations/00XX_rename_q_columns.py
from django.db import migrations

# Ajusta esto si tu tabla tiene otro esquema/nombre:
SCHEMA = "public"
TABLE = "auditoria_auditoriavisita"  # nombre por defecto para AuditoriaVisita

SQL = f"""
DO $$
BEGIN
  -- q9_internet_categoria -> internet_categoria
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q9_internet_categoria'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='internet_categoria'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q9_internet_categoria TO internet_categoria';
  END IF;

  -- q9_internet_otro -> internet_otro
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q9_internet_otro'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='internet_otro'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q9_internet_otro TO internet_otro';
  END IF;

  -- q10_tv_categoria -> tv_categoria
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q10_tv_categoria'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='tv_categoria'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q10_tv_categoria TO tv_categoria';
  END IF;

  -- q10_tv_otro -> tv_otro
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q10_tv_otro'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='tv_otro'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q10_tv_otro TO tv_otro';
  END IF;

  -- q11_otro_descripcion -> otro_descripcion
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q11_otro_descripcion'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='otro_descripcion'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q11_otro_descripcion TO otro_descripcion';
  END IF;

  -- q12_descripcion_problema -> descripcion_problema
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q12_descripcion_problema'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='descripcion_problema'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q12_descripcion_problema TO descripcion_problema';
  END IF;

  -- q18_llegada_comentarios -> llegada_comentarios
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q18_llegada_comentarios'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='llegada_comentarios'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q18_llegada_comentarios TO llegada_comentarios';
  END IF;

  -- q20_proceso_comentarios -> proceso_comentarios
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q20_proceso_comentarios'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='proceso_comentarios'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q20_proceso_comentarios TO proceso_comentarios';
  END IF;

  -- q22_config_comentarios -> config_comentarios
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q22_config_comentarios'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='config_comentarios'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q22_config_comentarios TO config_comentarios';
  END IF;

  -- q24_cierre_comentarios -> cierre_comentarios
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q24_cierre_comentarios'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='cierre_comentarios'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q24_cierre_comentarios TO cierre_comentarios';
  END IF;

  -- q25_percepcion -> percepcion
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q25_percepcion'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='percepcion'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q25_percepcion TO percepcion';
  END IF;

  -- q71_agend_comentarios -> agend_comentarios
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q71_agend_comentarios'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='agend_comentarios'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q71_agend_comentarios TO agend_comentarios';
  END IF;

  -- q73_desc_hfc -> desc_hfc
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q73_desc_hfc'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='desc_hfc'
  ) THEN
    EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN q73_desc_hfc TO desc_hfc';
  END IF;
END
$$;
"""

REVERSE = f"""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='internet_categoria')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q9_internet_categoria')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN internet_categoria TO q9_internet_categoria'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='internet_otro')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q9_internet_otro')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN internet_otro TO q9_internet_otro'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='tv_categoria')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q10_tv_categoria')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN tv_categoria TO q10_tv_categoria'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='tv_otro')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q10_tv_otro')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN tv_otro TO q10_tv_otro'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='otro_descripcion')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q11_otro_descripcion')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN otro_descripcion TO q11_otro_descripcion'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='descripcion_problema')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q12_descripcion_problema')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN descripcion_problema TO q12_descripcion_problema'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='llegada_comentarios')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q18_llegada_comentarios')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN llegada_comentarios TO q18_llegada_comentarios'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='proceso_comentarios')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q20_proceso_comentarios')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN proceso_comentarios TO q20_proceso_comentarios'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='config_comentarios')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q22_config_comentarios')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN config_comentarios TO q22_config_comentarios'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='cierre_comentarios')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q24_cierre_comentarios')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN cierre_comentarios TO q24_cierre_comentarios'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='percepcion')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q25_percepcion')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN percepcion TO q25_percepcion'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='agend_comentarios')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q71_agend_comentarios')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN agend_comentarios TO q71_agend_comentarios'; END IF;

  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='desc_hfc')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='{SCHEMA}' AND table_name='{TABLE}' AND column_name='q73_desc_hfc')
  THEN EXECUTE 'ALTER TABLE {SCHEMA}.{TABLE} RENAME COLUMN desc_hfc TO q73_desc_hfc'; END IF;
END
$$;
"""

class Migration(migrations.Migration):

    dependencies = [
        # >>> REEMPLAZA por la última migración aplicada de 'auditoria', ej:
        # ("auditoria", "0007_add_auditoria_fields")
        ("auditoria", "0009_alter_auditoriavisita_options"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql=REVERSE),
    ]
