# Generated by Django 2.2.6 on 2019-11-03 06:01

import bookplaylist.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_auto_20191102_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playlistbook',
            name='description',
            field=bookplaylist.models.NullTextField(blank=True, null=True, verbose_name='description'),
        ),
    ]
