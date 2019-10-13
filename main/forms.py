from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Playlist, PlaylistBook,
)


class SearchForm(forms.Form):
    q = forms.CharField(
        label = _('Search words')
    )


class PlaylistForm(forms.ModelForm):

    class Meta:
        model = Playlist
        fields = ('title', 'description', )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.user = self.user
        return super().save(commit=commit)
