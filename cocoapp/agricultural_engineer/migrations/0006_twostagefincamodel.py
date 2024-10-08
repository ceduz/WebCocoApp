# Generated by Django 5.0.4 on 2024-08-18 22:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agricultural_engineer', '0005_remove_beastpronosticmodel_prectotcorr_and_more'),
        ('farmer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TwoStageFincaModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Irrigation_and_drainage', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Fecha de modificación')),
                ('finca', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='farmer.finca', verbose_name='Nombre de la finca')),
            ],
            options={
                'ordering': ['created'],
            },
        ),
    ]
