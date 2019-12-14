from django.db import models


__all__ = ['NullCharField', 'NullEmailField', 'NullSlugField', 'NullTextField', 'NullURLField']


class NullFieldMixin:

    def get_prep_value(self, value):
        value = super().get_prep_value(value) if value else None
        return value

    def from_db_value(self, value, expression, connection):
        return value or ''


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
