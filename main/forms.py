from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Playlist, PlaylistBook, Theme,
)


class BasePlaylistForm(forms.ModelForm):
    use_required_attribute = False

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        for fieldname in self.fields:
            self.fields[fieldname].required = False

    def clean(self):
        if self.request.method == 'POST' and 'add_book' not in self.request.POST:
            for fieldname in self.fields:
                self.fields[fieldname].required = True
        return super().clean()

    def save(self, commit=True):
        return super().save(commit=commit)


class PlaylistForm(BasePlaylistForm):

    class Meta:
        model = Playlist
        fields = ('title', 'theme', 'description',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = _('Playlist\'s title')
        self.fields['theme'].empty_label = _('Free theme')
        self.fields['title'].widget.attrs['placeholder'] = _('Describe us the overview')
        self.fields['description'].widget.attrs['placeholder'] = _('Tell us why you are create this playlist')

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
        self.fields['description'].widget.attrs['placeholder'] = _('Please explain why you recommend this book')


DELETION_FIELD_NAME = 'DELETE'


class HiddenDeleteBaseInlineFormSet(forms.BaseInlineFormSet):

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.can_delete:
            form.fields[DELETION_FIELD_NAME] = forms.BooleanField(
                label=_('Delete'),
                required=False,
                widget=forms.HiddenInput(
                    attrs={
                        'class': 'delete-input'
                    }
                )
            )


PlaylistBookFormSet = forms.inlineformset_factory(
    parent_model=Playlist,
    model=PlaylistBook,
    form=PlaylistBookForm,
    formset=HiddenDeleteBaseInlineFormSet,
    extra=0,
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
    theme = forms.ModelChoiceField(
        Theme.objects.all(),
        to_field_name='slug',
        required=False,
        label = _('Theme'),
        empty_label=_('All themes'),
    )

    def __init__(self, q='', theme=None, *args, **kwargs):
        super().__init__(q=q, *args, **kwargs)
        self.fields['theme'].initial = theme
        self.fields['q'].widget.attrs['placeholder'] = _('Input theme, title and so on')


class BookSearchForm(SearchForm):

    def __init__(self, q='', theme=None, *args, **kwargs):
        super().__init__(q=q, *args, **kwargs)
        self.fields['q'].widget.attrs['placeholder'] = _('Input title or author name')
