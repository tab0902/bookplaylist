from django import forms
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _

from .models import (
    Playlist, PlaylistBook, Theme,
)
from bookplaylist.utils import SendEmailMixin


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
        self.fields['theme'].empty_label = None
        self.fields['title'].widget.attrs['placeholder'] = '例）不思議な恋愛'
        self.fields['description'].widget.attrs['placeholder'] \
            = '例）わたしが読んできたさまざまな恋愛に関係した本の中から、特に強く印象に残っているものをピックアップして紹介します。'
        if 'theme' in self.request.GET:
            self.fields['theme'].initial = Theme.objects.filter(slug=self.request.GET.get('theme')).first()
        else:
            self.fields['theme'].initial = Theme.objects.filter(slug=settings.SLUG_NO_THEME).first()
        if 'title' in self.request.GET:
            self.fields['title'].initial = self.request.GET.get('title')

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
        self.fields['description'].widget.attrs['placeholder'] = '例）幻想的で不思議な雰囲気を味わいたいひとにおすすめの一冊です。'


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
    mode = forms.CharField(widget=forms.HiddenInput)
    pk = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, mode=None, pk=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mode'].initial = mode
        self.fields['pk'].initial = pk
        self.fields['q'].widget.attrs['autofocus'] = True
        self.fields['q'].widget.attrs['placeholder'] = _('Input title name')


class ContactForm(forms.Form, SendEmailMixin):
    inquiry = forms.ChoiceField(
        label=_('Content of inquiry'),
        choices=settings.CONTACT_INQUIRY,
    )
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    url = forms.URLField(
        label=_('URL of the target page (option)'),
        required=False
    )
    body = forms.CharField(
        label=_('Body'),
        widget=forms.Textarea
    )

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if request.user.is_authenticated:
            self.fields['email'].initial = request.user.email

    def save(self, commit=True, domain_override=None,
             subject_template_name='main/contact_subject.html',
             email_template_name='main/contact_email.html',
             subject_template_name_admin='main/contact_subject_admin.html',
             email_template_name_admin='main/contact_email_admin.html',
             email_admin=settings.ADMIN_EMAIL,
             use_https=False,
             from_email=None, request=None,
             html_email_template_name=None, html_email_template_name_admin=None,
             extra_email_context=None):
        inquiry = dict(self.fields['inquiry'].choices)[self.cleaned_data['inquiry']]
        email = self.cleaned_data['email']
        url = self.cleaned_data['url']
        body = self.cleaned_data['body']
        user = request.user if request.user.is_authenticated else _('Guest user')

        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        context = {
            'inquiry': inquiry,
            'url': url,
            'body': body,
            'domain': domain,
            'site_name': site_name,
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        context_admin = {
            'user': user,
            'email': email,
            'inquiry': inquiry,
            'url': url,
            'body': body,
            'domain': domain,
            'site_name': site_name,
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        self.send_mail(
            subject_template_name, email_template_name, context, from_email,
            email, html_email_template_name=html_email_template_name,
        )
        self.send_mail(
            subject_template_name_admin, email_template_name_admin, context_admin, from_email,
            email_admin, html_email_template_name=html_email_template_name_admin,
        )
