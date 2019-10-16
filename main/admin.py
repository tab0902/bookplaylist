from django.contrib import admin

from .models import (
    Book, Category, Playlist, PlaylistBook,
)

# Register your models here.


class PlaylistInline(admin.TabularInline):
    model = Playlist
    can_delete = True
    show_change_link = True

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.playlist_set.count()
        return max_num


class PlaylistBookInline(admin.TabularInline):
    model = Playlist.books.through
    can_delete = True
    show_change_link = False

    def get_extra(self, request, obj=None, **kwargs):
        extra = 1
        if obj:
            return extra - obj.books.count() if extra > obj.books.count() else 0
        return extra


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sequence', 'created_at', )
    list_filter = ('created_at', 'updated_at', )
    search_fields = ('name', 'description', )


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'author', 'publisher', 'pubdate', )
    list_filter = ('created_at', 'updated_at', )
    search_fields = ('isbn', 'title', 'title_collation_key', 'volume', 'series', 'publisher', 'pubdate', 'cover', 'author', 'amazon_url', )


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'created_at', )
    list_filter = ('category__name', 'created_at', 'updated_at', )
    search_fields = ('title', 'description', 'user__username', 'category__name', 'books__title', 'books__author', )
    inlines = [PlaylistBookInline]
