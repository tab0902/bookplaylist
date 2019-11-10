# Generated by Django 2.2.6 on 2019-11-09 08:01

import bookplaylist.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_auto_20191103_1501'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playlist',
            name='category',
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', bookplaylist.models.NullCharField(max_length=50, unique=True, verbose_name='theme name')),
                ('slug', bookplaylist.models.NullSlugField(blank=True, null=True, unique=True, verbose_name='slug')),
                ('sequence', models.SmallIntegerField(blank=True, null=True, verbose_name='sequence')),
                ('description', bookplaylist.models.NullTextField(blank=True, null=True, verbose_name='description')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date updated')),
            ],
            options={
                'verbose_name': 'theme',
                'verbose_name_plural': 'themes',
                'db_table': 'themes',
                'ordering': ['sequence'],
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='theme',
            index=models.Index(fields=['sequence'], name='sequence'),
        ),
        migrations.AddIndex(
            model_name='theme',
            index=models.Index(fields=['created_at'], name='created_at'),
        ),
        migrations.AddIndex(
            model_name='theme',
            index=models.Index(fields=['updated_at'], name='updated_at'),
        ),
        migrations.AddField(
            model_name='playlist',
            name='theme',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='main.Theme', verbose_name='theme'),
        ),
        migrations.RunSQL(
            "ALTER TABLE `playlists` MODIFY `theme_id` CHAR(32) AFTER `user_id`",
            migrations.RunSQL.noop,
        ),
    ]