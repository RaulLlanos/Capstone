from django.db import migrations, models

# --- SQL para la vista (copiado desde 0002) ---
SQL_CREATE_VIEW = """
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

SQL_DROP_VIEW = "DROP VIEW IF EXISTS usuarios_sistema;"
# --- Fin SQL para la vista ---


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_change_rol_length_and_choices'),
    ]

    operations = [
        # Modelo 'proxy' para la vista (no crea tabla, solo representa)
        migrations.CreateModel(
            name='UsuarioSistema',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('rol', models.CharField(max_length=20)), # Mantén el tipo original aquí
                ('is_active', models.BooleanField()),
                ('date_joined', models.DateTimeField()),
            ],
            options={
                'verbose_name': 'Usuario (sistema)',
                'verbose_name_plural': 'Usuarios (sistema)',
                'db_table': 'usuarios_sistema',
                'managed': False, # Django no gestionará esta 'tabla' (vista)
            },
        ),

        # 1. Eliminar la vista ANTES de alterar el campo
        migrations.RunSQL(SQL_DROP_VIEW, reverse_sql=SQL_CREATE_VIEW),

        # 2. Alterar el campo 'rol' en la tabla 'usuarios_usuario'
        migrations.AlterField(
            model_name='usuario',
            name='rol',
            field=models.CharField(
                choices=[('tecnico', 'Técnico'), ('administrador', 'Administrador')],
                default='tecnico',
                max_length=20, # Asegúrate que coincida con el nuevo tamaño si cambió
                verbose_name='Rol'
            ),
        ),

        # 3. Volver a crear la vista DESPUÉS de alterar el campo
        migrations.RunSQL(SQL_CREATE_VIEW, reverse_sql=SQL_DROP_VIEW),
        ]