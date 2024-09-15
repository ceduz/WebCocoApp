# Generated by Django 5.0.4 on 2024-07-10 14:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researcher', '0002_remove_forecastscenarios_finca_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mergescenarios',
            name='finca',
        ),
        migrations.AddField(
            model_name='mergescenarios',
            name='cod_forecast_scen',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='researcher.forecastscenarios', verbose_name='Código de generados de escenarios'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mergescenarios',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
    ]