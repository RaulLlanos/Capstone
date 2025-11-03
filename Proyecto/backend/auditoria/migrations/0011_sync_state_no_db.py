from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("auditoria", "0010_rename_q_columns"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Internet (Q9)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="internet_categoria",
                    field=models.CharField(max_length=32, blank=True, choices=[
                        ("lento", "Navegaba muy lento"),
                        ("wifi_alcance", "Señal del Wifi con bajo alcance"),
                        ("cortes", "Cortes/Días sin servicio"),
                        ("intermitencia", "Intermitencia de la Señal de Internet"),
                        ("otro", "Otro"),
                    ]),
                ),
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="internet_otro",
                    field=models.CharField(max_length=200, blank=True),
                ),
                # TV (Q10)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="tv_categoria",
                    field=models.CharField(max_length=32, blank=True, choices=[
                        ("sin_senal", "Me quedaba sin señal de TV"),
                        ("pixelado", "Se pixelaba la imagen de TV"),
                        ("intermitencia", "Intermitencia de la Señal"),
                        ("desfase", "Presenta desfase con la señal en vivo"),
                        ("streaming", "Problemas con Plataforma de Streaming"),
                        ("zapping", "Problemas con zapping (lentitud)"),
                        ("equipos", "Problemas con Equipos (Dbox, Control, IPTV)"),
                        ("otro", "Otro"),
                    ]),
                ),
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="tv_otro",
                    field=models.CharField(max_length=200, blank=True),
                ),
                # Otro (Q11)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="otro_descripcion",
                    field=models.TextField(blank=True),
                ),
                # Solo HFC (Q73)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="desc_hfc",
                    field=models.TextField(blank=True),
                ),
                # AGENDAMIENTO (Q71)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="agend_comentarios",
                    field=models.TextField(blank=True),
                ),
                # Llegada (Q18)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="llegada_comentarios",
                    field=models.TextField(blank=True),
                ),
                # Proceso (Q20)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="proceso_comentarios",
                    field=models.TextField(blank=True),
                ),
                # Config (Q22)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="config_comentarios",
                    field=models.TextField(blank=True),
                ),
                # Cierre (Q24)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="cierre_comentarios",
                    field=models.TextField(blank=True),
                ),
                # Percepción (Q25)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="percepcion",
                    field=models.TextField(blank=True),
                ),
                # Finalizar (Q12)
                migrations.AlterField(
                    model_name="auditoriavisita",
                    name="descripcion_problema",
                    field=models.TextField(blank=True),
                ),
            ],
            database_operations=[],
        ),
    ]
