from django.db import models


class PublishedOnlyManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)
