# Generated by Django 5.1.7 on 2025-05-23 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cinema', '0010_alter_bannerfon_image_back'),
    ]

    operations = [
        migrations.AlterField(
            model_name='film',
            name='type_film',
            field=models.CharField(max_length=200),
        ),
    ]
