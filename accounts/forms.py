from django import forms
from django.contrib.auth import (
    get_user_model, password_validation,
)
from django.contrib.auth.forms import (
    AuthenticationForm as BaseAuthenticationForm, ReadOnlyPasswordHashField, UserChangeForm as BaseUserChangeForm, UserCreationForm as BaseUserCreationForm, UsernameField,
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from bookplaylist.utils import SendEmailMixin

UserModel = get_user_model()


class UserCreationForm(BaseUserCreationForm):

    class Meta:
        model = UserModel
        fields = ('username', 'email', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].required = True


class UserChangeForm(BaseUserChangeForm):

    class Meta:
        model = UserModel
        fields = '__all__'


class UserSettingsForm(forms.ModelForm):

    class Meta(UserChangeForm.Meta):
        model = UserModel
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].help_text = None


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserModel
        fields = ('comment',)


class PasswordCreationForm(forms.Form):
    error_messages = {
        'password_mismatch': _('The two password fields didn’t match.'),
    }
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'autofocus': True, 'placeholder': _('At least 8 characters')}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': _('Enter the same password')}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user

    @property
    def changed_data(self):
        data = super().changed_data
        for name in self.fields:
            if name not in data:
                return []
        return ['password']


class AuthenticationForm(BaseAuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _('Username or Email Address')
        self.fields['username'].widget.attrs['autofocus'] = False


class SignupForm(UserCreationForm, SendEmailMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = _('Letters, numbers, and _ characters')
        self.fields['email'].widget.attrs['placeholder'] = _('Enter a valid email address')
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
        self.fields['password1'].widget.attrs['placeholder'] = _('At least 8 characters')
        self.fields['password2'].widget.attrs['placeholder'] = _('Enter the same password')

    def save(self, commit=True, domain_override=None,
             subject_template_name='accounts/signup_subject.html',
             email_template_name='accounts/signup_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        user = super().save(commit=False)
        user.is_active = False
        email = self.cleaned_data["email"]

        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        context = {
            'email': email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token_generator.make_token(user),
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        self.send_mail(
            subject_template_name, email_template_name, context, from_email,
            email, html_email_template_name=html_email_template_name,
        )

        if commit:
            user.save()

        return user


class VerificationAgainForm(forms.Form, SendEmailMixin):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    def get_users(self, email):
        active_users = UserModel._default_manager.filter(**{
            '%s__iexact' % UserModel.get_email_field_name(): email,
            'is_active': False,
            'date_verified': None,
        })
        return (u for u in active_users if u.has_usable_password())

    def save(self, commit=True, domain_override=None,
             subject_template_name='accounts/verification_again_subject.html',
             email_template_name='accounts/verification_again_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        email = self.cleaned_data["email"]

        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                email, html_email_template_name=html_email_template_name,
            )


class DeacrivateForm(forms.ModelForm):

    class Meta:
        model = UserModel
        fields = ('reason_for_deactivation',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason_for_deactivation'].required = True
