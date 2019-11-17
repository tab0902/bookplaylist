from django.contrib import admin

from .models import (
    Book, BookData, Playlist, PlaylistBook, Provider, Theme,
)
from bookplaylist.admin import (
    Admin, AllObjectsForeignKeyMixin, AllObjectsMixin, SlimTabularInline, StackedInline, TabularInline,
)

# Register your models here.


class BookDataInline(AllObjectsForeignKeyMixin, StackedInline):
    model = BookData
    can_delete = False
    show_change_link = True

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlist_set.count()
        return max_num


class PlaylistInline(AllObjectsMixin, AllObjectsForeignKeyMixin, SlimTabularInline):
    model = Playlist
    can_delete = True
    show_change_link = True

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlist_set.count()
        return max_num


class PlaylistBookTabularInline(AllObjectsForeignKeyMixin, TabularInline):
    model = Book.playlists.through
    can_delete = True
    show_change_link = False
    exclude = ('deleted_at', 'description',)

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlists.count()
        return max_num


class PlaylistBookStackedInline(StackedInline):
    model = Playlist.books.through
    can_delete = True
    show_change_link = False

    def get_extra(self, request, obj=None, **kwargs):
        extra = 1
        if obj:
            return extra - obj.playlist_book_set.count() if extra > obj.playlist_book_set.count() else 0
        return extra


@admin.register(Theme)
class ThemeAdmin(Admin):
    list_display = ('name', 'slug', 'sequence', 'created_at', )
    list_filter = ('created_at', 'updated_at', )
    search_fields = ('name', 'slug', 'description', )
    inlines = (PlaylistInline,)


@admin.register(Provider)
class ProviderAdmin(AllObjectsMixin, Admin):
    list_display = ('name', 'slug', 'priority', 'is_available', 'created_at', )
    list_filter = ('is_available', 'created_at', 'updated_at', )
    search_fields = ('name', 'slug', 'description', )


@admin.register(Book)
class BookAdmin(Admin):
    list_display = ('__str__', 'isbn', 'created_at', )
    list_filter = ('created_at', 'updated_at', )
    search_fields = ('isbn', 'book_data__title', 'book_data__author', 'book_data__publisher', 'book_data__cover', 'book_data__affiliate_url', )
    inlines = (BookDataInline, PlaylistBookTabularInline,)


@admin.register(Playlist)
class PlaylistAdmin(AllObjectsMixin, AllObjectsForeignKeyMixin, Admin):
    list_display = ('title', 'user', 'theme', 'created_at', 'is_published', )
    list_filter = ('theme__name', 'is_published', 'created_at', 'updated_at', )
    search_fields = ('title', 'description', 'user__username', 'theme__name', 'books__isbn', 'books__book_data__title', 'books__book_data__author', 'books__book_data__publisher', )
    inlines = (PlaylistBookStackedInline,)
