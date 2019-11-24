# Generated by Django 2.2.6 on 2019-11-22 06:48

import accounts.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_user_deleted_at'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', accounts.models.UserManager()),
                ('all_objects_without_deleted', accounts.models.UserWithInactiveManager()),
                ('all_objects', accounts.models.AllUserManager()),
            ],
        ),
    ]