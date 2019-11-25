from django.db import models
from django.utils import timezone


class QuerySet(models.QuerySet):

    def delete(self):
        return super().update(updated_at=timezone.now(), deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class AllObjectsQuerySet(QuerySet):

    def restore(self):
        return super().update(updated_at=timezone.now(), deleted_at=None)

    def only_deleted(self):
        return self.filter(deleted_at__isnull=False)
