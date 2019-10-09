from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from bookplaylist.models import BaseModel

# Create your models here.


class Book(BaseModel):
    playlists = models.ManyToManyField(
        'Playlist',
        through='PlaylistBook',
        through_fields=('book', 'playlist'),
        verbose_name=_('playlists'),
        blank=True,
    )
    isbn = models.CharField(_('ISBN'), max_length=13, unique=True)
    title = models.CharField(_('title'), max_length=255)
    title_collation_key = models.CharField(_('collation key'), max_length=255, blank=True, null=True)
    volume = models.CharField(_('volume'), max_length=50, blank=True, null=True)
    series = models.CharField(_('series'), max_length=255, blank=True, null=True)
    publisher = models.CharField(_('publisher'), max_length=255, blank=True, null=True)
    pubdate = models.CharField(_('date published'), max_length=10, blank=True, null=True)
    cover = models.URLField(_('cover'), blank=True, null=True)
    author = models.CharField(_('author'), max_length=255, blank=True, null=True)
    amazon_url = models.URLField(_('Amazon URL'), blank=True, null=True)

    class Meta:
        db_table = 'books'
        ordering = ['isbn']
        verbose_name = _('book')
        verbose_name_plural = _('books')

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
    title = models.CharField(_('title'), max_length=50)
    description = models.TextField(_('description'))

    class Meta:
        db_table = 'playlists'
        ordering = ['-created_at']
        verbose_name = _('playlist')
        verbose_name_plural = _('playlists')

    def __str__(self):
        return '%s' % self.title


class PlaylistBook(BaseModel):
    playlist = models.ForeignKey('Playlist', on_delete=models.CASCADE, verbose_name=_('playlist'))
    book = models.ForeignKey('Book', on_delete=models.PROTECT, verbose_name=_('book'))
    description = models.TextField(_('description'))

    class Meta:
        db_table = 'playlists_books'
        ordering = ['playlist', 'book']
        verbose_name = _('book in playlist')
        verbose_name_plural = _('books in playlists')

    def __str__(self):
        return '%s' % self.book
