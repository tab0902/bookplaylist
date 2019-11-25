# Generated by Django 2.2.6 on 2019-11-25 03:50

from django.db import migrations, models
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_playlist_card'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playlist',
            name='card',
        ),
        migrations.AddField(
            model_name='playlist',
            name='og_image',
            field=models.ImageField(blank=True, null=True, upload_to=main.models.Playlist.get_og_image_path, verbose_name='Open Graph image'),
        ),
        migrations.RunSQL(
            "ALTER TABLE `playlists` MODIFY `og_image` varchar(100) AFTER `description`",
            migrations.RunSQL.noop,
        ),
    ]