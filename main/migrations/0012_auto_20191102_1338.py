# Generated by Django 2.2.6 on 2019-11-02 04:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_auto_20191102_1049'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='playlistbook',
            options={'ordering': ['playlist', 'created_at'], 'verbose_name': 'book in playlist', 'verbose_name_plural': 'books in playlists'},
        ),
    ]
