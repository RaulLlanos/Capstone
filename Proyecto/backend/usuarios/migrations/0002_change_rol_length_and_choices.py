# usuarios/migrations/00xx_create_usuarios_sistema_view.py
from django.db import migrations

SQL_CREATE = """
CREATE OR REPLACE VIEW usuarios_sistema AS
SELECT
  id,
  first_name,
  last_name,
  email,
  rol,
  is_active,
  date_joined
FROM public.usuarios;
"""

SQL_DROP = "DROP VIEW IF EXISTS usuarios_sistema;"

class Migration(migrations.Migration):
    dependencies = [
        # ⚠️ Reemplaza por la última migración REAL de 'usuarios'
        ("usuarios", "0001_initial"),
    ]
    operations = [
        migrations.RunSQL(SQL_CREATE, SQL_DROP),
    ]
