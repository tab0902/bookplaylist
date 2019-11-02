from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from bookplaylist.models import (
    BaseModel, NullCharField, NullSlugField, NullTextField, NullURLField,
)

# Create your models here.


class Category(BaseModel):
    name = NullCharField(_('category name'), max_length=50, unique=True)
    slug = NullSlugField(_('slug'), unique=True)
    sequence = models.SmallIntegerField(_('sequence'))
    description = NullTextField(_('description'), blank=True, null=True)

    class Meta(BaseModel.Meta):
        db_table = 'categories'
        ordering = ['sequence']
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        indexes = [
            models.Index(fields=['name'], name='name'),
            models.Index(fields=['sequence'], name='sequence'),
        ] + BaseModel._meta.indexes

    def __str__(self):
        return '%s' % self.name


class Book(BaseModel):
    playlists = models.ManyToManyField(
        'Playlist',
        through='PlaylistBook',
        through_fields=('book', 'playlist'),
        verbose_name=_('playlists'),
        blank=True,
    )
    isbn = NullCharField(_('ISBN'), max_length=13, unique=True)
    title = NullCharField(_('title'), max_length=255, blank=True, null=True)
    title_collation_key = NullCharField(_('collation key'), max_length=255, blank=True, null=True)
    volume = NullCharField(_('volume'), max_length=255, blank=True, null=True)
    series = NullCharField(_('series'), max_length=255, blank=True, null=True)
    publisher = NullCharField(_('publisher'), max_length=255, blank=True, null=True)
    pubdate = NullCharField(_('date published'), max_length=255, blank=True, null=True)
    cover = NullURLField(_('cover'), blank=True, null=True)
    author = NullCharField(_('author'), max_length=255, blank=True, null=True)
    amazon_url = NullURLField(_('Amazon URL'), blank=True, null=True)

    class Meta(BaseModel.Meta):
        db_table = 'books'
        ordering = ['isbn']
        verbose_name = _('book')
        verbose_name_plural = _('books')
        indexes = [
            models.Index(fields=['title'], name='title'),
            models.Index(fields=['publisher'], name='publisher'),
            models.Index(fields=['pubdate'], name='pubdate'),
            models.Index(fields=['author'], name='author'),
        ] + BaseModel._meta.indexes + [
            models.Index(fields=['title', 'volume', 'series'], name='idx01'),
            models.Index(fields=['pubdate', 'title'], name='idx02'),
            models.Index(fields=['title', 'title_collation_key', 'author'], name='idx03'),
        ]

    def __str__(self):
        return '%s' % self.title


class Playlist(BaseModel):
    books = models.ManyToManyField(
        'Book',
        through='PlaylistBook',
        through_fields=('playlist', 'book'),
        verbose_name=_('books'),
    )
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name=_('user'))
    category = models.ForeignKey('Category', on_delete=models.PROTECT, verbose_name=_('category'))
    title = NullCharField(_('title'), max_length=50)
    description = NullTextField(_('description'))

    class Meta(BaseModel.Meta):
        db_table = 'playlists'
        ordering = ['-created_at']
        verbose_name = _('playlist')
        verbose_name_plural = _('playlists')
        indexes = [
            models.Index(fields=['title'], name='title'),
        ] + BaseModel._meta.indexes + [
            models.Index(fields=['user', 'created_at'], name='idx01'),
        ]

    def __str__(self):
        return '%s' % self.title


class PlaylistBook(BaseModel):
    playlist = models.ForeignKey('Playlist', on_delete=models.CASCADE, verbose_name=_('playlist'))
    book = models.ForeignKey('Book', on_delete=models.PROTECT, verbose_name=_('book'), to_field='isbn', db_column='book_isbn')
    description = NullTextField(_('description'))

    class Meta(BaseModel.Meta):
        db_table = 'playlists_books'
        ordering = ['playlist', 'book']
        verbose_name = _('book in playlist')
        verbose_name_plural = _('books in playlists')

    def __str__(self):
        return '%s' % self.book
