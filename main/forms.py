from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Playlist, PlaylistBook,
)

class InlineFormSetMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formset = self.formset_class(
            instance=self.instance,
            data=self.data if self.is_bound else None,
        )

    def is_valid(self):
        return super().is_valid() and self.formset.is_valid()

    def save(self, commit=True):
        instance = super().save(commit)
        self.formset.save(commit)
        return instance


class BasePlaylistForm(forms.ModelForm):
    use_required_attribute = False

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        for fieldname in self.fields:
            self.fields[fieldname].required = False

    def clean(self):
        if  self.request.method == 'POST' and 'add_book' not in self.request.POST:
            for fieldname in self.fields:
                self.fields[fieldname].required = True
        return super().clean()

    def save(self, commit=True):
        return super().save(commit=commit)


class PlaylistForm(BasePlaylistForm):

    class Meta:
        model = Playlist
        fields = ('title', 'description',)

    def save(self, commit=True):
        self.instance.user = self.request.user
        return super().save(commit=commit)


class PlaylistBookForm(BasePlaylistForm):

    class Meta:
        model = PlaylistBook
        fields = ('book', 'description',)

    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields['book'].widget = forms.HiddenInput()


PlaylistBookFormSet = forms.inlineformset_factory(
    parent_model=Playlist,
    model=PlaylistBook,
    form=PlaylistBookForm,
    extra=0,
)


class SearchForm(forms.Form):
    q = forms.CharField(
        label = _('Search words')
    )
