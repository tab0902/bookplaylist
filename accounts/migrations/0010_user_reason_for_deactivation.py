# Generated by Django 2.2.6 on 2019-11-30 06:24

import bookplaylist.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_auto_20191130_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='reason_for_deactivation',
            field=bookplaylist.models.fields.NullTextField(blank=True, null=True, verbose_name='reason for deactivation'),
        ),
        migrations.RunSQL(
            "ALTER TABLE `users` MODIFY `reason_for_deactivation` longtext AFTER `hopes_newsletter`",
            migrations.RunSQL.noop,
        ),
    ]
