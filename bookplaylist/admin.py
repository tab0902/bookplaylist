from django import forms
from django.contrib import admin
from django.db import models

class SlimTabularInline(admin.TabularInline):
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 5, 'cols': 50})},
    }


class AllObjectsModelAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = self.model.all_objects.get_queryset()
        return qs
