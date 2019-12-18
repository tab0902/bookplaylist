import imgkit
import re

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from bookplaylist.models import (
    BaseModel, Manager, NullCharField, NullSlugField, NullTextField, NullURLField, get_file_path, remove_emoji,
)
from .manager import (
    AllLikeManager, AllPlaylistManager, BookDataManager, BookManager, LikeManager, PlaylistBookManager, PlaylistManager, PlaylistWithUnpublishedManager, ProviderManager,
)

# Create your models here.


class Theme(BaseModel):
    name = NullCharField(_('theme name'), max_length=50)
    slug = NullSlugField(_('slug'), blank=True, null=True)
    sequence = models.SmallIntegerField(_('sequence'), blank=True, null=True)
    description = NullTextField(_('description'), blank=True, null=True)

    class Meta(BaseModel.Meta):
        db_table = 'themes'
        ordering = ['sequence']
        verbose_name = _('theme')
        verbose_name_plural = _('themes')
        indexes = [
            models.Index(fields=['name'], name='name'),
            models.Index(fields=['slug'], name='slug'),
            models.Index(fields=['sequence'], name='sequence'),
        ] + BaseModel._meta.indexes
        constraints = [
            models.UniqueConstraint(fields=['name'], condition=models.Q(deleted_at__isnull=True), name='name'),
            models.UniqueConstraint(fields=['slug'], condition=models.Q(deleted_at__isnull=True), name='slug'),
        ]

    def __str__(self):
        return '%s' % self.name


class Provider(BaseModel):
    name = NullCharField(_('provider name'), max_length=50)
    slug = NullSlugField(_('slug'))
    endpoint = NullURLField(_('endpoint'))
    priority = models.SmallIntegerField(_('priority'))
    description = NullTextField(_('description'), blank=True, null=True)
    is_available = models.BooleanField(_('available'), default=True)
    objects = ProviderManager()
    all_objects_without_deleted = Manager()

    class Meta(BaseModel.Meta):
        db_table = 'providers'
        ordering = ['priority']
        verbose_name = _('provider')
        verbose_name_plural = _('providers')
        indexes = [
            models.Index(fields=['name'], name='name'),
            models.Index(fields=['slug'], name='slug'),
            models.Index(fields=['priority'], name='priority'),
        ] + BaseModel._meta.indexes
        constraints = [
            models.UniqueConstraint(fields=['name'], condition=models.Q(deleted_at__isnull=True), name='name'),
            models.UniqueConstraint(fields=['slug'], condition=models.Q(deleted_at__isnull=True), name='slug'),
            models.UniqueConstraint(fields=['priority'], condition=models.Q(deleted_at__isnull=True), name='priority'),
        ]

    def __str__(self):
        return '%s' % self.name


BOOK_DATA_FIELDS = ('provider', 'title', 'author', 'publisher', 'cover', 'large_cover', 'affiliate_url')


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
    def _default_data(self):
        return self.book_data_set.first()

    class Meta(BaseModel.Meta):
        db_table = 'books'
        ordering = ['isbn']
        verbose_name = _('book')
        verbose_name_plural = _('books')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in BOOK_DATA_FIELDS:
            self._set_property_from_field_of_book_data(field)

    def __str__(self):
        return '%s' % (self.book_data_set.first() or self.isbn)

    def _set_property_from_field_of_book_data(self, field):
        prop = property(lambda self: self._get_field_of_book_data(field))
        setattr(self.__class__, field, prop)

    def _get_field_of_book_data(self, field):
        book_data = self.book_data_set.all()
        for book_datum in book_data:
            value = getattr(book_datum, field)
            if value:
                return value
        return getattr(book_data.first(), field) if book_data.first() else None



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
        constraints = [
            models.UniqueConstraint(fields=['book', 'provider'], name='book_isbn_provider_id_uniq'),
        ]

    def __str__(self):
        return '%s' % self.title


def get_og_image_path(instance, filename):
    return get_file_path(instance, filename, field='og_image')


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
        book_count = self.playlist_book_set.count()
        if book_count < 6:
            template = get_template('main/playlists/og_image/{}.html'.format(book_count))
        else:
            template = get_template('main/playlists/og_image/6.html')
        raw_title = self.title
        self.title = remove_emoji(raw_title.strip())
        context = {'playlist': self}
        options = {
            'width': str(settings.OG_IMAGE_WIDTH),
            'height': str(settings.OG_IMAGE_HEIGHT),
            'encoding': 'UTF-8',
            'quiet': '',
        }
        img = imgkit.from_string(template.render(context), False, options=options)
        self.title = raw_title
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
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'book'], condition=models.Q(deleted_at__isnull=True), name='playlist_id_book_isbn_uniq'),
        ]

    def __str__(self):
        return '%s' % self.book


class Like(BaseModel):
    playlist = models.ForeignKey('Playlist', on_delete=models.CASCADE, related_name='likes', related_query_name='like', verbose_name=_('playlist'))
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='likes', related_query_name='like', verbose_name=_('user'))
    message = NullTextField(_('message'), blank=True, null=True)
    date_notified = models.DateTimeField(_('date notified'), blank=True, null=True)
    objects = LikeManager()
    all_objects = AllLikeManager()

    class Meta(BaseModel.Meta):
        db_table = 'likes'
        ordering = ['playlist', 'created_at']
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        indexes = BaseModel._meta.indexes + [
            models.Index(fields=['playlist', 'created_at'], name='idx01'),
            models.Index(fields=['user', 'created_at'], name='idx02'),
            models.Index(fields=['playlist', 'date_notified', 'created_at'], name='idx03'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'user'], condition=models.Q(deleted_at__isnull=True), name='playlist_id_user_id_uniq'),
        ]

    def __str__(self):
        return '%s' % self.user
