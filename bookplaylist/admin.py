from django import forms
from django.contrib import admin
from django.db import models


class TabularInline(admin.TabularInline):
    exclude = ('deleted_at',)


class StackedInline(admin.StackedInline):
    exclude = ('deleted_at',)


class Admin(admin.ModelAdmin):
    exclude = ('deleted_at',)


class SlimTabularInline(TabularInline):
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 5, 'cols': 50})},
    }


class AllObjectsModelAdmin(Admin):

    def get_queryset(self, request):
        qs = self.model.all_objects_without_deleted.get_queryset()
        return qs
