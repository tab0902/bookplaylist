# Generated by Django 2.2.6 on 2019-12-11 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_auto_20191211_1234'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['nickname'], name='nickname'),
        ),
    ]
