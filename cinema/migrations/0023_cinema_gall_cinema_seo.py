# Generated by Django 5.1.7 on 2025-06-10 18:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0022_remove_cinema_hall_hall_cinema'),
    ]

    operations = [
        migrations.AddField(
            model_name='cinema',
            name='gall',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cinema.gallery'),
        ),
        migrations.AddField(
            model_name='cinema',
            name='seo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cinema.seo'),
        ),
    ]
