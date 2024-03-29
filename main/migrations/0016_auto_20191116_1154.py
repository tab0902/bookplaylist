# Generated by Django 2.2.6 on 2019-11-16 02:54

import bookplaylist.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_playlist_is_published'),
    ]

    operations = [
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', bookplaylist.models.NullCharField(max_length=50, verbose_name='provider name')),
                ('slug', bookplaylist.models.NullSlugField(unique=True, verbose_name='slug')),
                ('endpoint', bookplaylist.models.NullURLField(verbose_name='endpoint')),
                ('priority', models.SmallIntegerField(unique=True, verbose_name='priority')),
                ('description', bookplaylist.models.NullTextField(blank=True, null=True, verbose_name='description')),
                ('is_available', models.BooleanField(default=True, verbose_name='available')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date updated')),
            ],
            options={
                'verbose_name': 'provider',
                'verbose_name_plural': 'providers',
                'db_table': 'providers',
                'ordering': ['priority'],
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='provider',
            index=models.Index(fields=['created_at'], name='created_at'),
        ),
        migrations.AddIndex(
            model_name='provider',
            index=models.Index(fields=['updated_at'], name='updated_at'),
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='title',
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='publisher',
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='pubdate',
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='author',
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='idx01',
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='idx02',
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='idx03',
        ),
        migrations.RemoveField(
            model_name='book',
            name='amazon_url',
        ),
        migrations.RemoveField(
            model_name='book',
            name='author',
        ),
        migrations.RemoveField(
            model_name='book',
            name='cover',
        ),
        migrations.RemoveField(
            model_name='book',
            name='pubdate',
        ),
        migrations.RemoveField(
            model_name='book',
            name='publisher',
        ),
        migrations.RemoveField(
            model_name='book',
            name='series',
        ),
        migrations.RemoveField(
            model_name='book',
            name='title',
        ),
        migrations.RemoveField(
            model_name='book',
            name='title_collation_key',
        ),
        migrations.RemoveField(
            model_name='book',
            name='volume',
        ),
        migrations.CreateModel(
            name='BookData',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('book', models.ForeignKey(db_column='book_isbn', on_delete=django.db.models.deletion.CASCADE, related_name='book_data_set', to='main.Book', to_field='isbn', verbose_name='book')),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='book_data_set', to='main.Provider', verbose_name='provider')),
                ('title', bookplaylist.models.NullCharField(max_length=255, verbose_name='title')),
                ('author', bookplaylist.models.NullCharField(blank=True, max_length=255, null=True, verbose_name='author')),
                ('publisher', bookplaylist.models.NullCharField(blank=True, max_length=255, null=True, verbose_name='publisher')),
                ('cover', bookplaylist.models.NullURLField(blank=True, null=True, verbose_name='cover')),
                ('affiliate_url', bookplaylist.models.NullURLField(blank=True, null=True, verbose_name='Affiliate URL')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date updated')),
            ],
            options={
                'verbose_name': 'book data',
                'verbose_name_plural': 'book data',
                'db_table': 'book_data',
                'ordering': ['book', 'provider'],
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='bookdata',
            index=models.Index(fields=['title'], name='title'),
        ),
        migrations.AddIndex(
            model_name='bookdata',
            index=models.Index(fields=['author'], name='author'),
        ),
        migrations.AddIndex(
            model_name='bookdata',
            index=models.Index(fields=['publisher'], name='publisher'),
        ),
        migrations.AddIndex(
            model_name='bookdata',
            index=models.Index(fields=['created_at'], name='created_at'),
        ),
        migrations.AddIndex(
            model_name='bookdata',
            index=models.Index(fields=['updated_at'], name='updated_at'),
        ),
        migrations.AlterUniqueTogether(
            name='bookdata',
            unique_together={('book', 'provider')},
        ),
    ]
