from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .forms import (
    UserChangeForm, UserCreationForm,
)
from .models import User
from main.admin import PlaylistInline
from bookplaylist.admin import (
    AllObjectsForeignKeyMixin, AllObjectsMixin,
)

# Register your models here.


@admin.register(User)
class UserAdmin(AllObjectsMixin, AllObjectsForeignKeyMixin, BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('pk', 'username', 'email', 'twitter_id', 'facebook_id', 'password', )}),
        (_('Personal info'), {'fields': ('comment', 'last_name', 'first_name', 'hopes_newsletter', )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'date_verified', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', ),
        }),
    )
    readonly_fields = ('pk', )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('username', 'email', 'last_login', 'date_joined', 'is_staff', 'is_active', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'hopes_newsletter', 'groups', 'last_login', 'date_joined', 'date_verified', )
    search_fields = ('username', 'email', 'twitter_id', 'facebook_id', 'first_name', 'last_name', 'comment', )
    ordering = ('-last_login', )
    filter_horizontal = ('groups', 'user_permissions', )
    inlines = [PlaylistInline]
