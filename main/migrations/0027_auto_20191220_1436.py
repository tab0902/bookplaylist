# Generated by Django 2.2.6 on 2019-12-20 05:36

from django.db import migrations, models
import django.conf
import django.db.models.deletion


def add_theme_to_playlist_with_no_theme(apps, schema_editor):
    Theme = apps.get_model('main', 'Theme')
    Playlist = apps.get_model('main', 'Playlist')
    db_alias = schema_editor.connection.alias
    theme_free, _ = Theme.objects.using(db_alias).get_or_create(
        slug=django.conf.settings.SLUG_NO_THEME,
        defaults = {
            'name': 'テーマ自由',
            'sequence': 99,
        }
    )
    Playlist.objects.using(db_alias).filter(theme__isnull=True).update(theme=theme_free)


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_auto_20191219_2149'),
    ]

    operations = [
        migrations.RunPython(
            add_theme_to_playlist_with_no_theme,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='playlist',
            name='theme',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.Theme', verbose_name='theme'),
        ),
    ]
