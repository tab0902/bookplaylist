import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_('date created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date updated'), auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at'], name='created_at'),
            models.Index(fields=['updated_at'], name='updated_at'),
        ]


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
