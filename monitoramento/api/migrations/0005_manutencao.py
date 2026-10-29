import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auditlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='Manutencao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_manutencao', models.DateTimeField(db_index=True)),
                ('descricao', models.TextField()),
                ('responsavel', models.CharField(max_length=150)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('sensor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='manutencoes', to='api.sensor')),
            ],
            options={
                'verbose_name': 'manutenção',
                'verbose_name_plural': 'manutenções',
                'db_table': 'manutencoes',
                'ordering': ['-data_manutencao'],
                'indexes': [models.Index(fields=['sensor', 'data_manutencao'], name='manut_sensor_data_idx')],
            },
        ),
    ]
