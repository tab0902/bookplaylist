import os
import uuid

from django.core.exceptions import (
    NON_FIELD_ERRORS, ValidationError,
)
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

    @property
    def is_deleted(self):
        return True if self.deleted_at else False

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

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        unique_checks_conditional = self._get_unique_checks_conditional(exclude=exclude)
        errors = self._perform_unique_checks_conditional(unique_checks_conditional)
        if errors:
            raise ValidationError(errors)

    def _get_unique_checks_conditional(self, exclude=None):
        if exclude is None:
            exclude = []
        unique_checks_conditional = []

        constraints = [(self.__class__, self._meta.constraints)]
        for parent_class in self._meta.get_parent_list():
            if parent_class._meta.constraints:
                constraints.append((parent_class, parent_class._meta.constraints))\

        for model_class, model_constraints in constraints:
            for constraint in model_constraints:
                if (isinstance(constraint, models.UniqueConstraint) and
                        constraint.condition is not None and
                        not any(name in exclude for name in constraint.fields)):
                    unique_checks_conditional.append((model_class, constraint.fields, constraint.condition))
        return unique_checks_conditional

    def _perform_unique_checks_conditional(self, unique_checks_conditional):
        errors = {}

        for model_class, unique_check, condition in unique_checks_conditional:
            lookup_kwargs = {}
            for field_name in unique_check:
                f = self._meta.get_field(field_name)
                lookup_value = getattr(self, f.attname)
                if (lookup_value is None or
                        (lookup_value == '' and connection.features.interprets_empty_strings_as_nulls)):
                    continue
                if f.primary_key and not self._state.adding:
                    continue
                lookup_kwargs[str(field_name)] = lookup_value

            if len(unique_check) != len(lookup_kwargs):
                continue

            qs = model_class._default_manager.filter(condition, **lookup_kwargs)

            model_class_pk = self._get_pk_val(model_class._meta)
            if not self._state.adding and model_class_pk is not None:
                qs = qs.exclude(pk=model_class_pk)
            if qs.exists():
                if len(unique_check) == 1:
                    key = unique_check[0]
                else:
                    key = NON_FIELD_ERRORS
                errors.setdefault(key, []).append(self.unique_error_message(model_class, unique_check))

        return errors
