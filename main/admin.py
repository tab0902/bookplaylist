from django.contrib import admin

from .models import (
    Book, BookData, Like, Playlist, PlaylistBook, Provider, Theme,
)
from bookplaylist.admin import (
    Admin, AllObjectsForeignKeyMixin, AllObjectsMixin, SlimTabularInline, StackedInline, TabularInline,
)

# Register your models here.


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


class PlaylistInline(AllObjectsMixin, AllObjectsForeignKeyMixin, SlimTabularInline):
    model = Playlist
    can_delete = False
    show_change_link = True
    fields = ('title', 'theme', 'user', 'og_image', 'created_at', 'is_published',)
    readonly_fields = ('created_at',)

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlist_set.count()
        return max_num

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('theme')

    def has_change_permission(self, request, obj=None):
        return False


class PlaylistBookTabularInline(AllObjectsForeignKeyMixin, TabularInline):
    model = PlaylistBook
    can_delete = False
    show_change_link = False
    fields = ('playlist', 'created_at',)
    readonly_fields = ('playlist', 'created_at',)

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


@admin.register(Theme)
class ThemeAdmin(Admin):
    list_display = ('name', 'slug', 'sequence', 'created_at',)
    list_filter = ('created_at', 'updated_at',)
    search_fields = ('name', 'slug', 'description',)
    inlines = [PlaylistInline]


@admin.register(Provider)
class ProviderAdmin(AllObjectsMixin, Admin):
    list_display = ('name', 'slug', 'priority', 'is_available', 'created_at',)
    list_filter = ('is_available', 'created_at', 'updated_at',)
    search_fields = ('name', 'slug', 'description',)


@admin.register(Book)
class BookAdmin(Admin):
    list_display = ('__str__', 'isbn', 'created_at',)
    list_filter = ('created_at', 'updated_at',)
    search_fields = ('isbn', 'book_data__title', 'book_data__author', 'book_data__publisher', 'book_data__cover', 'book_data__affiliate_url',)
    inlines = [BookDataInline, PlaylistBookTabularInline]


@admin.register(Playlist)
class PlaylistAdmin(AllObjectsMixin, AllObjectsForeignKeyMixin, Admin):
    fields = ('title', 'user', 'theme', 'description', 'og_image', 'pk', 'created_at', 'updated_at', 'is_published',)
    list_display = ('title', 'user', 'theme', 'created_at', 'is_published',)
    list_filter = ('theme__name', 'is_published', 'created_at', 'updated_at',)
    search_fields = ('title', 'description', 'user__username', 'theme__name', 'playlist_book__description', 'playlist_book__book__isbn', 'playlist_book__book__book_data__title', 'playlist_book__book__book_data__author', 'playlist_book__book__book_data__publisher',)
    inlines = [PlaylistBookStackedInline, LikeInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('theme')

    def get_readonly_fields(self, request, obj=None):
        EXCLUDE = ('is_published',)
        if not request.user.is_superuser:
            self.readonly_fields = tuple(
                [f.name for f in self.opts.local_fields if f.name not in EXCLUDE] +
                ['pk']
            )
        return super().get_readonly_fields(request, obj)
