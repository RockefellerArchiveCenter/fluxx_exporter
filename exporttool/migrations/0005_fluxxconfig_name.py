# Generated by Django 5.0.3 on 2024-04-23 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exporttool', '0004_fluxxconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='fluxxconfig',
            name='name',
            field=models.CharField(default='MainConfig', max_length=100),
            preserve_default=False,
        ),
    ]
