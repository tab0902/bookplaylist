from bookplaylist.models import (
    AllObjectsManager, Manager,
)
from .query import (
    AllPlaylistQuerySet, PlaylistQuerySet,
)


__all__ = ['ProviderManager', 'BookManager', 'BookDataManager', 'PlaylistManager', 'PlaylistWithUnpublishedManager', 'AllPlaylistManager', 'PlaylistBookManager']


# Provider
class ProviderManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)


# Book
class BookManager(Manager):

    def get_queryset(self):
        return super().get_queryset().prefetch_related('book_data_set')


# BookData
class BookDataManager(Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('provider')


# Playlist
class BasePlaylistManager(Manager.from_queryset(PlaylistQuerySet)):

    def get_queryset(self):
        return super().get_queryset().prefetch_related('playlist_book_set')


class PlaylistManager(BasePlaylistManager):

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True, user__is_active=True, user__deleted_at__isnull=True)


class PlaylistWithUnpublishedManager(BasePlaylistManager):

    def get_queryset(self):
        return super().get_queryset().filter(user__deleted_at__isnull=True)


class AllPlaylistManager(AllObjectsManager.from_queryset(AllPlaylistQuerySet)):
    pass


# PlaylistBook
class PlaylistBookManager(Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('book').prefetch_related('book__book_data_set')
