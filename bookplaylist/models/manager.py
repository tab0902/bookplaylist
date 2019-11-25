from django.db import models

from .query import (
    AllObjectsQuerySet, QuerySet,
)


class Manager(models.Manager.from_queryset(QuerySet)):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


AllObjectsManager = models.Manager.from_queryset(AllObjectsQuerySet)
