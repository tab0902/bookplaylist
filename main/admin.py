from urllib.parse import urlparse

from django.contrib import admin
from django.db.models import F, Prefetch
from django.urls import resolve
from django.utils.translation import gettext_lazy as _

from .models import (
    Book, BookData, Like, Playlist, PlaylistBook, Provider, Recommendation, Template, Theme,
)
from bookplaylist.admin import (
    Admin, AllObjectsForeignKeyMixin, AllObjectsMixin, SlimTabularInline, StackedInline, TabularInline,
)

# Register your models here.


class AutocompleteJsonView(admin.views.autocomplete.AutocompleteJsonView):

    def get_queryset(self):
        qs = self.queryset or self.model_admin.get_queryset(self.request)
        qs, search_use_distinct = self.model_admin.get_search_results(self.request, qs, self.term)
        if search_use_distinct:
            qs = qs.distinct()
        return qs


class BookDataInline(AllObjectsForeignKeyMixin, StackedInline):
    model = BookData
    can_delete = False
    show_change_link = True
    readonly_fields = ('pk', 'created_at', 'updated_at',)

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.book_data_set.count()
        return max_num


class ThemeInline(TabularInline):
    model = Theme
    can_delete = False
    show_change_link = True
    fields = ('name', 'slug', 'sequence', 'created_at',)
    readonly_fields = fields

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.theme_set.count()
        return max_num


class PlaylistInline(AllObjectsMixin, AllObjectsForeignKeyMixin, SlimTabularInline):
    model = Playlist
    can_delete = False
    show_change_link = True
    fields = ('title', 'theme', 'user', 'og_image', 'created_at', 'is_published',)
    readonly_fields = fields

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlist_set.count()
        return max_num

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('theme')


class PlaylistBookTabularInline(AllObjectsForeignKeyMixin, TabularInline):
    model = PlaylistBook
    can_delete = False
    show_change_link = False
    fields = ('playlist', 'created_at',)
    readonly_fields = fields

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlist_book_set.count()
        return max_num


class PlaylistBookStackedInline(AllObjectsForeignKeyMixin, StackedInline):
    model = PlaylistBook
    can_delete = True
    show_change_link = False
    readonly_fields = ('pk', 'created_at', 'updated_at',)
    raw_id_fields = ('book',)

    def get_extra(self, request, obj=None, **kwargs):
        extra = 1
        if obj:
            return extra - obj.playlist_book_set.count() if extra > obj.playlist_book_set.count() else 0
        return extra

    def get_autocomplete_fields(self, request):
        # PlaylistBook.book can't be put in autocomplete_fields
        # because its db_column is not id but isbn.
        return tuple([f for f in self.autocomplete_fields if f != 'book'])


class RecommendationInline(TabularInline):
    model = Recommendation
    can_delete = True
    show_change_link = False
    fields = ('playlist', 'sequence', 'updated_at',)
    readonly_fields = ('updated_at',)

    def get_extra(self, request, obj=None, **kwargs):
        extra = 4
        if obj:
            return extra - obj.recommendation_set.count() if extra > obj.recommendation_set.count() else 0
        return extra


class LikeInline(SlimTabularInline):
    model = Like
    can_delete = False
    show_change_link = False
    readonly_fields = ('created_at', 'date_notified',)

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.likes.count()
        return max_num


@admin.register(Template)
class TemplateAdmin(Admin):
    fields = ('name', 'slug', 'book_numbers', 'pk', 'created_at', 'updated_at',)
    list_display = ('name', 'slug', 'created_at',)
    list_filter = ('created_at', 'updated_at',)
    search_fields = ('name', 'slug',)
    filter_horizontal = ('book_numbers',)
    inlines = [ThemeInline]


@admin.register(Theme)
class ThemeAdmin(Admin):
    list_display = ('name', 'slug', 'template', 'created_at', 'sequence',)
    list_editable = ('sequence',)
    list_filter = ('template', 'created_at', 'updated_at',)
    search_fields = ('name', 'slug', 'description',)
    inlines = [RecommendationInline, PlaylistInline]


@admin.register(Provider)
class ProviderAdmin(AllObjectsMixin, Admin):
    list_display = ('name', 'slug', 'created_at', 'is_available', 'priority',)
    list_filter = ('is_available', 'created_at', 'updated_at',)
    list_editable = ('priority',)
    search_fields = ('name', 'slug', 'description',)


@admin.register(Book)
class BookAdmin(Admin):
    list_display = ('__str__', 'isbn', 'created_at',)
    list_filter = ('created_at', 'updated_at',)
    search_fields = ('isbn', 'book_data__title', 'book_data__author', 'book_data__publisher', 'book_data__cover', 'book_data__affiliate_url',)
    inlines = [BookDataInline, PlaylistBookTabularInline]


class IsPublishedListFilter(admin.SimpleListFilter):
    parameter_name = 'is_published'

    def __init__(self, request, params, model, model_admin):
        self.title = model_admin.model._meta.get_field('is_published').verbose_name
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        return (
            (['1', None], _('Yes')),
            (['0'],  _('No')),
        )

    def queryset(self, request, queryset):
        published = {
            'is_published': True,
            'user__is_active': True,
        }
        if self.value() in ('1', None):
            return queryset.filter(**published)
        elif self.value() == '0':
            return queryset.exclude(**published)
        else:
            return queryset.none()

    def choices(self, changelist):
        for lookups, title in self.lookup_choices:
            yield {
                'selected': self.value() in lookups,
                'query_string': changelist.get_query_string({self.parameter_name: lookups[0]}),
                'display': title,
            }


@admin.register(Playlist)
class PlaylistAdmin(AllObjectsMixin, AllObjectsForeignKeyMixin, Admin):
    fields = ('title', 'user', 'theme', 'description', 'og_image', 'pk', 'created_at', 'updated_at', 'sequence', 'is_published',)
    list_display = ('title', 'user', 'theme', 'created_at', 'sequence', 'is_published',)
    list_editable = ('sequence',)
    list_filter = (IsPublishedListFilter, 'theme__name', 'created_at', 'updated_at',)
    search_fields = ('title', 'description', 'user__username', 'theme__name', 'playlist_book__description', 'playlist_book__book__isbn', 'playlist_book__book__book_data__title', 'playlist_book__book__book_data__author', 'playlist_book__book__book_data__publisher',)
    ordering = (F('sequence').asc(nulls_last=True), '-created_at')
    inlines = [PlaylistBookStackedInline, LikeInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('theme')

    def get_readonly_fields(self, request, obj=None):
        EXCLUDE = ('sequence', 'is_published',)
        if not request.user.is_superuser:
            self.readonly_fields = tuple(
                [f.name for f in self.opts.local_fields if f.name not in EXCLUDE] +
                ['pk']
            )
        return super().get_readonly_fields(request, obj)

    def _get_parent_object_from_referer(self, request, parent_model):
        path = urlparse(request.META.get('HTTP_REFERER')).path
        resolved = resolve(path)
        if resolved.kwargs and 'object_id' in resolved.kwargs:
            parent_obj = parent_model.objects.get(id=resolved.kwargs['object_id'])
        elif resolved.args:
            parent_obj = parent_model.objects.get(id=resolved.args[0])
        else:
            parent_obj = None
        return parent_obj

    def autocomplete_view(self, request):
        conditions = {}
        theme = self._get_parent_object_from_referer(request, parent_model=Theme)
        if theme:
            conditions['theme'] = theme
        queryset = Playlist.objects.filter(**conditions).select_related(None).prefetch_related(None)
        return AutocompleteJsonView.as_view(model_admin=self, queryset=queryset)(request)
