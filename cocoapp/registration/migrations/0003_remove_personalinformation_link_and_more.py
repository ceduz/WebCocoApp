# Generated by Django 5.0.4 on 2024-08-22 03:28

import registration.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_personalinformation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='personalinformation',
            name='link',
        ),
        migrations.AlterField(
            model_name='personalinformation',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to=registration.models.custom_upload_to),
        ),
    ]
