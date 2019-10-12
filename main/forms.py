from django import forms
from django.utils.translation import gettext_lazy as _


class PlaylistSearchForm(forms.Form):
    query = forms.CharField(
        label = _('Search words')
    )
