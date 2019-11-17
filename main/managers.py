from bookplaylist.models import Manager


class PublishedOnlyManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class AvailableOnlyManager(Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_available=True)
