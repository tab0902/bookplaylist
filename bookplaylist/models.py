import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


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


class Manager(models.Manager.from_queryset(QuerySet)):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


AllObjectsManager = models.Manager.from_queryset(AllObjectsQuerySet)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_('date created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date updated'), auto_now=True)
    deleted_at = models.DateTimeField(_('date deleted'), blank=True, null=True)
    objects = Manager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at'], name='created_at'),
            models.Index(fields=['updated_at'], name='updated_at'),
        ]

    def delete(self):
        if not self.deleted_at:
            self.deleted_at = timezone.now()
            self.save()

    def restore(self):
        if self.deleted_at:
            self.deleted_at = None
            self.save()

    def hard_delete(self):
        super().delete()


class NullFieldMixin:

    def get_prep_value(self, value):
        value = super().get_prep_value(value) if value else None
        return value


class NullCharField(NullFieldMixin, models.CharField):
    pass


class NullEmailField(NullFieldMixin, models.EmailField):
    pass


class NullSlugField(NullFieldMixin, models.SlugField):
    pass


class NullTextField(NullFieldMixin, models.TextField):
    pass


class NullURLField(NullFieldMixin, models.URLField):
    pass
