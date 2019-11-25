from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import models

from main.models import (
    Playlist, Provider,
)


UserModel = get_user_model()


class TabularInline(admin.TabularInline):
    exclude = ('deleted_at', )


class StackedInline(admin.StackedInline):
    exclude = ('deleted_at', )


class Admin(admin.ModelAdmin):
    exclude = ('deleted_at', )
    readonly_fields = ('pk', 'created_at', 'updated_at', )


class SlimTabularInline(TabularInline):
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 5, 'cols': 50})},
    }


class AllObjectsMixin:

    def get_queryset(self, request):
        qs = self.model.all_objects_without_deleted.get_queryset()
        return qs


class AllObjectsForeignKeyMixin:

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'playlist':
            kwargs['queryset'] = Playlist.all_objects_without_deleted.all()
        elif db_field.name == 'provider':
            kwargs['queryset'] = Provider.all_objects_without_deleted.all()
        elif db_field.name == 'user':
            kwargs['queryset'] = UserModel.all_objects_without_deleted.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
