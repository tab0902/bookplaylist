from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .forms import (
    UserCreationForm, UserChangeForm,
)
from .models import User
from main.admin import PlaylistInline

# Register your models here.


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'twitter_id', 'facebook_id', 'password', )}),
        (_('Personal info'), {'fields': ('comment', 'last_name', 'first_name', 'is_verified', 'hopes_newsletter', )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', ),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('username', 'email', 'twitter_id', 'facebook_id', 'is_staff', 'last_login', 'date_joined', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'hopes_newsletter', 'groups', 'last_login', 'date_joined', )
    search_fields = ('username', 'email', 'twitter_id', 'facebook_id', 'first_name', 'last_name', 'comment', )
    ordering = ('-last_login', )
    filter_horizontal = ('groups', 'user_permissions', )
    inlines = [PlaylistInline]
