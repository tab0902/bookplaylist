import os
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .manager import (
    AllObjectsManager, Manager
)

# Create your models here.


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


class FileModel(BaseModel):

    class Meta:
        abstract = True

    def _get_file_path(self, filename, field, filetype='img'):
        directory = os.path.join(filetype, self.__class__._meta.db_table, field)
        filename = str(self.pk) + os.path.splitext(filename)[-1]
        path = os.path.join(directory, filename)
        return path
