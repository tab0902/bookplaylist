from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Category, Playlist, PlaylistBook,
)


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
        fields = ('title', 'category', 'description',)

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
    can_delete=False,
)


class SearchForm(forms.Form):
    q = forms.CharField(
        label = _('Key words')
    )

    def __init__(self, q='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['q'].initial = q
        self.fields['q'].widget.attrs['placeholder'] = _('Input key words')


class PlaylistSearchForm(SearchForm):
    category = forms.ModelChoiceField(
        Category.objects.all(),
        to_field_name='slug',
        required=False,
        label = _('Category'),
        empty_label=_('All categories'),
    )

    def __init__(self, q='', category=None, *args, **kwargs):
        super().__init__(q=q, *args, **kwargs)
        self.fields['category'].initial = category
        self.fields['q'].widget.attrs['placeholder'] = _('Input theme, title and so on')


class BookSearchForm(SearchForm):

    def __init__(self, q='', category=None, *args, **kwargs):
        super().__init__(q=q, *args, **kwargs)
        self.fields['q'].widget.attrs['placeholder'] = _('Input title or author name')
