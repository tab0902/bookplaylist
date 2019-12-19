from bookplaylist.models import (
    AllObjectsManager, Manager,
)
from .query import (
    AllPlaylistQuerySet, PlaylistQuerySet,
)


__all__ = ['ProviderManager', 'BookManager', 'AllBookManager', 'BookDataManager', 'PlaylistManager', 'PlaylistWithUnpublishedManager', 'AllPlaylistManager', 'PlaylistBookManager', 'LikeManager', 'AllLikeManager']


############
# Provider #
############

class ProviderManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)


########
# Book #
########

class BookManagerMixin:

    def get_queryset(self):
        return super().get_queryset().prefetch_related('book_data_set')


class BookManager(BookManagerMixin, Manager):
    pass


class AllBookManager(BookManagerMixin, AllObjectsManager):
    pass


############
# BookData #
############

class BookDataManagerMixin:

    def get_queryset(self):
        return super().get_queryset().select_related('provider')


class BookDataManager(BookDataManagerMixin, Manager):
    pass


class AllBookDataManager(BookDataManagerMixin, AllObjectsManager):
    pass


############
# Playlist #
############

class PlaylistManagerMixin:

    def get_queryset(self):
        return super().get_queryset().select_related('user').prefetch_related('playlist_book_set', 'likes')


class PlaylistManager(PlaylistManagerMixin, Manager.from_queryset(PlaylistQuerySet)):

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True, user__is_active=True, user__deleted_at__isnull=True)


class PlaylistWithUnpublishedManager(PlaylistManagerMixin, Manager.from_queryset(PlaylistQuerySet)):

    def get_queryset(self):
        return super().get_queryset().filter(user__deleted_at__isnull=True)


class AllPlaylistManager(PlaylistManagerMixin, AllObjectsManager.from_queryset(AllPlaylistQuerySet)):
    pass


################
# PlaylistBook #
################

class PlaylistBookManagerMixin:

    def get_queryset(self):
        return super().get_queryset().select_related('book').prefetch_related('book__book_data_set')


class PlaylistBookManager(PlaylistBookManagerMixin, Manager):
    pass


class AllPlaylistBookManager(PlaylistBookManagerMixin, AllObjectsManager):
    pass


########
# Like #
########

class LikeManagerMixin:

    def get_queryset(self):
        return super().get_queryset().select_related('playlist', 'user')


class LikeManager(LikeManagerMixin, Manager):
    pass


class AllLikeManager(LikeManagerMixin, AllObjectsManager):
    pass
