# Generated by Django 2.2.6 on 2019-12-11 00:48

import bookplaylist.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_user_reason_for_deactivation'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='nickname',
            field=bookplaylist.models.fields.NullCharField(blank=True, max_length=50, null=True, verbose_name='nickname'),
        ),
        migrations.RunSQL(
            "ALTER TABLE `users` MODIFY `nickname` varchar(50) AFTER `password`",
            migrations.RunSQL.noop,
        ),
    ]
