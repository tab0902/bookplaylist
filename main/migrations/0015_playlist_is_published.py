# Generated by Django 2.2.6 on 2019-11-12 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_auto_20191109_1701'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='is_published',
            field=models.BooleanField(default=True, verbose_name='published'),
        ),
        migrations.RunSQL(
            "ALTER TABLE `playlists` MODIFY `is_published` bool DEFAULT b'1' NOT NULL AFTER `description`",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE `playlists` ALTER COLUMN `is_published` DROP DEFAULT",
            migrations.RunSQL.noop,
        ),
    ]
