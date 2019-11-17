from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from bookplaylist.models import (
    BaseModel, Manager, NullCharField, NullSlugField, NullTextField, NullURLField,
)

# Create your models here.


class Theme(BaseModel):
    name = NullCharField(_('theme name'), max_length=50, unique=True)
    slug = NullSlugField(_('slug'), blank=True, null=True, unique=True)
    sequence = models.SmallIntegerField(_('sequence'), blank=True, null=True)
    description = NullTextField(_('description'), blank=True, null=True)

    class Meta(BaseModel.Meta):
        db_table = 'themes'
        ordering = ['sequence']
        verbose_name = _('theme')
        verbose_name_plural = _('themes')
        indexes = [
            models.Index(fields=['sequence'], name='sequence'),
        ] + BaseModel._meta.indexes

    def __str__(self):
        return '%s' % self.name


class ProviderManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)


class Provider(BaseModel):
    name = NullCharField(_('provider name'), max_length=50)
    slug = NullSlugField(_('slug'), unique=True)
    endpoint = NullURLField(_('endpoint'))
    priority = models.SmallIntegerField(_('priority'), unique=True)
    description = NullTextField(_('description'), blank=True, null=True)
    is_available = models.BooleanField(_('available'), default=True)
    objects = ProviderManager()
    all_objects_without_deleted = Manager()

    class Meta(BaseModel.Meta):
        db_table = 'providers'
        ordering = ['priority']
        verbose_name = _('provider')
        verbose_name_plural = _('providers')

    def __str__(self):
        return '%s' % self.name


class BookManager(Manager):

    def get_queryset(self):
        return super().get_queryset().prefetch_related('book_data_set')


class Book(BaseModel):
    playlists = models.ManyToManyField(
        'Playlist',
        through='PlaylistBook',
        through_fields=('book', 'playlist'),
        verbose_name=_('playlists'),
        blank=True,
    )
    isbn = NullCharField(_('ISBN'), max_length=13, unique=True)
    objects = BookManager()

    @property
    def data(self):
        return self.book_data_set.first()

    class Meta(BaseModel.Meta):
        db_table = 'books'
        ordering = ['isbn']
        verbose_name = _('book')
        verbose_name_plural = _('books')

    def __str__(self):
        return '%s' % (self.book_data_set.first() or self.isbn)


class BookData(BaseModel):
    book = models.ForeignKey(
        'Book',
        on_delete=models.CASCADE,
        to_field='isbn',
        db_column='book_isbn',
        related_name='book_data_set',
        related_query_name='book_data',
        verbose_name=_('book')
    )
    provider = models.ForeignKey(
        'Provider',
        on_delete=models.CASCADE,
        related_name='book_data_set',
        related_query_name='book_data',
        verbose_name=_('provider')
    )
    title = NullCharField(_('title'), max_length=255)
    author = NullCharField(_('author'), max_length=255, blank=True, null=True)
    publisher = NullCharField(_('publisher'), max_length=255, blank=True, null=True)
    cover = NullURLField(_('cover'), blank=True, null=True)
    affiliate_url = NullURLField(_('Affiliate URL'), blank=True, null=True)

    class Meta(BaseModel.Meta):
        db_table = 'book_data'
        ordering = ['book', 'provider']
        verbose_name = _('book data')
        verbose_name_plural = _('book data')
        indexes = [
            models.Index(fields=['title'], name='title'),
            models.Index(fields=['author'], name='author'),
            models.Index(fields=['publisher'], name='publisher'),
        ] + BaseModel._meta.indexes
        unique_together = [['book', 'provider']]

    def __str__(self):
        return '%s' % self.title


class PlaylistManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True, user__is_active=True, user__deleted_at__isnull=True)


class PlaylistWithUnpublishedManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(user__deleted_at__isnull=True)


class Playlist(BaseModel):
    books = models.ManyToManyField(
        'Book',
        through='PlaylistBook',
        through_fields=('playlist', 'book'),
        verbose_name=_('books'),
    )
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name=_('user'))
    theme = models.ForeignKey('Theme', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('theme'))
    title = NullCharField(_('title'), max_length=50)
    description = NullTextField(_('description'))
    is_published = models.BooleanField(_('published'), default=True)
    objects = PlaylistManager()
    all_objects_without_deleted = PlaylistWithUnpublishedManager()

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


class PlaylistBookManager(Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('book').prefetch_related('book__book_data_set')


class PlaylistBook(BaseModel):
    playlist = models.ForeignKey(
        'Playlist',
        on_delete=models.CASCADE,
        related_name='playlist_book_set',
        related_query_name='playlist_book',
        verbose_name=_('playlist')
    )
    book = models.ForeignKey(
        'Book',
        on_delete=models.PROTECT,
        to_field='isbn',
        db_column='book_isbn',
        related_name='playlist_book_set',
        related_query_name='playlist_book',
        verbose_name=_('book')
    )
    description = NullTextField(_('description'), blank=True, null=True)
    objects = PlaylistBookManager()

    class Meta(BaseModel.Meta):
        db_table = 'playlists_books'
        ordering = ['playlist', 'created_at']
        verbose_name = _('book in playlist')
        verbose_name_plural = _('books in playlists')
        unique_together = [['playlist', 'book']]

    def __str__(self):
        return '%s' % self.book
