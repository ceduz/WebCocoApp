# Generated by Django 5.0.4 on 2024-07-13 03:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('researcher', '0004_twostagemodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='twostagemodel',
            name='Irrigation_and_drainage',
            field=models.TextField(default=1),
            preserve_default=False,
        ),
    ]
