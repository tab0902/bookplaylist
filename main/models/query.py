from bookplaylist.models import (
    AllObjectsQuerySet, QuerySet,
)


__all__ = ['AllPlaylistQuerySet', 'PlaylistQuerySet']


# Playlist
class PlaylistQuerySetMixin:

    def hard_delete(self):
        for playlist in self.all():
            playlist.og_image.delete(save=False)
        return super().hard_delete()


class PlaylistQuerySet(PlaylistQuerySetMixin, QuerySet):
    pass


class AllPlaylistQuerySet(PlaylistQuerySetMixin, AllObjectsQuerySet):
    pass
