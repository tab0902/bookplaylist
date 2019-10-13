from django import forms
from django.utils.translation import gettext_lazy as _


class PlaylistSearchForm(forms.Form):
    q = forms.CharField(
        label = _('Search playlists')
    )
