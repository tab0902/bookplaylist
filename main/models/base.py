import imgkit
import os
import re
from functools import partial

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
    AllBookDataManager, AllBookManager, AllLikeManager, AllPlaylistBookManager, AllPlaylistManager, AllTemplateManager,
    BookDataManager, BookManager, LikeManager, PlaylistBookManager, PlaylistManager, PlaylistWithUnpublishedManager,
    ProviderManager, RecommendationManager, TemplateManager,
)

# Create your models here.


class Number(BaseModel):
    number = models.PositiveSmallIntegerField(_('number'), unique=True)

    class Meta(BaseModel.Meta):
        db_table = 'numbers'
        ordering = ['number']
        verbose_name = _('number')
        verbose_name_plural = _('numbers')

    def __str__(self):
        return '%s' % self.number


class Template(BaseModel):
    book_numbers = models.ManyToManyField(
        'Number',
        db_table='templates_numbers',
        related_name='templates',
        related_query_name='template',
        verbose_name=_('the avarable numbers of books')
    )
    name = NullCharField(_('template name'), max_length=50)
    slug = NullSlugField(_('slug'), unique=True)

    @property
    def directory(self):
        return 'main/playlists/og_image/{}'.format(self.slug)

    class Meta(BaseModel.Meta):
        db_table = 'templates'
        ordering = ['created_at']
        verbose_name = _('template')
        verbose_name_plural = _('templates')

    def __str__(self):
        return '%s' % self.name


def get_or_create_default_template():
    template, _ = Template.objects.get_or_create(slug='default', defaults={'name': 'デフォルト'})
    return template.pk


class Theme(BaseModel):
    template = models.ForeignKey(
        'Template',
        on_delete=models.PROTECT,
        default=get_or_create_default_template,
        verbose_name=_('template')
    )
    name = NullCharField(_('theme name'), max_length=50)
    slug = NullSlugField(_('slug'), blank=True, null=True)
    sequence = models.PositiveSmallIntegerField(_('sequence'), blank=True, null=True)
    description = NullTextField(_('description'), blank=True, null=True)

    @property
    def tagged_name(self):
        tag = '#' if self.slug != settings.SLUG_NO_THEME else ''
        name = self.name
        return '{}{}'.format(tag, name)

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
    priority = models.PositiveSmallIntegerField(_('priority'))
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
    isbn = NullCharField(_('ISBN'), max_length=13, unique=True)
    objects = BookManager()
    all_objects = AllBookManager()

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
    all_objects = AllBookDataManager()

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


class Playlist(BaseModel):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name=_('user'))
    theme = models.ForeignKey('Theme', on_delete=models.PROTECT, verbose_name=_('theme'))
    title = NullCharField(_('title'), max_length=50)
    description = NullTextField(_('description'))
    og_image = models.ImageField(
        upload_to=partial(get_file_path, field='og_image'),
        blank=True,
        null=True,
        verbose_name=_('Open Graph image')
    )
    sequence = models.PositiveSmallIntegerField(_('sequence'), blank=True, null=True)
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
            models.Index(fields=['sequence'], name='sequence'),
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
        template = self.theme.template
        template_dir = template.directory
        template_book_numbers = template.book_numbers.values_list('number', flat=True)

        book_count = self.playlist_book_set.count()
        book_numbers = [n for n in template_book_numbers if n <= book_count]
        book_number = max(book_numbers) if book_numbers else min(template_book_numbers)
        template_file = '{}.html'.format(book_number)
        template_path = os.path.join(template_dir, template_file)
        template = get_template(template_path)

        raw_title = self.title
        self.title = remove_emoji(raw_title.strip())
        context = {
            'playlist': self,
            'directory': template_dir,
        }
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
    all_objects = AllPlaylistBookManager()


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


class Recommendation(BaseModel):
    playlist = models.OneToOneField(
        'Playlist',
        on_delete=models.CASCADE,
        verbose_name=_('playlist')
    )
    theme = models.ForeignKey(
        'Theme',
        on_delete=models.CASCADE,
        verbose_name=_('theme')
    )
    sequence = models.PositiveSmallIntegerField(_('sequence'))
    objects = RecommendationManager()
    all_objects = RecommendationManager()

    class Meta(BaseModel.Meta):
        db_table = 'recommendations'
        ordering = ['theme', 'sequence']
        verbose_name = _('recommendation')
        verbose_name_plural = _('recommendations')
        indexes = [
            models.Index(fields=['sequence'], name='sequence'),
        ] + BaseModel._meta.indexes + [
            models.Index(fields=['theme', 'sequence'], name='idx01'),
        ]

    def __str__(self):
        return '%s' % self.playlist

    def delete(self):
        self.hard_delete()


class Like(BaseModel):
    playlist = models.ForeignKey(
        'Playlist',
        on_delete=models.CASCADE,
        related_name='likes',
        related_query_name='like',
        verbose_name=_('playlist')
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='likes',
        related_query_name='like',
        verbose_name=_('user')
    )
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
