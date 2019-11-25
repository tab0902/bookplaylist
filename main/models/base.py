import imgkit
import re

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from bookplaylist.models import (
    BaseModel, FileModel, Manager, NullCharField, NullSlugField, NullTextField, NullURLField,
)
from .manager import (
    AllPlaylistManager, BookDataManager, BookManager, PlaylistBookManager, PlaylistManager, PlaylistWithUnpublishedManager, ProviderManager,
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
    objects = BookDataManager()

    @property
    def large_cover(self):
        return re.sub(r'\?_ex=\d+x\d+', '', self.cover)

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


class Playlist(FileModel):

    def get_og_image_path(self, filename):
        return self._get_file_path(filename=filename, field='og_image')

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
    og_image = models.ImageField(upload_to=get_og_image_path, blank=True, null=True, verbose_name=_('Open Graph image'))
    is_published = models.BooleanField(_('published'), default=True)
    objects = PlaylistManager()
    all_objects_without_deleted = PlaylistWithUnpublishedManager()
    all_objects = AllPlaylistManager()

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

    def get_absolute_url(self):
        return reverse_lazy('main:playlist_detail', args=[str(self.pk)])

    def hard_delete(self):
        self.og_image.delete(save=False)
        super().hard_delete()

    def save_og_image(self, save=True):
        # save self.og_image
        book_count = self.playlist_book_set.count()
        if book_count < 6:
            template = get_template('main/playlists/og_image/{}.html'.format(book_count))
        else:
            template = get_template('main/playlists/og_image/6.html')
        context = {'playlist': self}
        options = {
            'encoding': 'UTF-8',
            'width': '1200',
            'height': '630',
            'quiet': '',
        }
        img = imgkit.from_string(template.render(context), False, options=options)
        self.og_image.save('{}.jpg'.format(str(self.pk)), ContentFile(img), save=save)


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