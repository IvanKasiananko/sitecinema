# Generated by Django 5.1.7 on 2025-07-17 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0029_alter_ticket_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cinema',
            name='adress',
            field=models.TextField(max_length=300),
        ),
    ]
