# Generated by Django 5.0.2 on 2024-03-28 03:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farmer', '0003_alter_inventory_due_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='due_date',
            field=models.DateTimeField(null=True, verbose_name='Fecha de vencimiento'),
        ),
    ]
