from django.contrib import messages
from django.contrib.auth import (
    get_user_model, login as auth_login, views as auth_views,
)
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    AuthenticationForm, PasswordCreationForm, SignupForm, UserSettingsForm, VerificationAgainForm,
)
from bookplaylist.views import (
    login_required, sensitive_post_parameters,
)

# Create your views here.


UserModel = get_user_model()


@login_required
class IndexView(generic.TemplateView):
    template_name = 'accounts/index.html'


@login_required
class SettingsView(generic.UpdateView):
    form_class = UserSettingsForm
    password_text = '************'
    password_link_text = _('Password change')
    success_url = reverse_lazy('accounts:settings')
    template_name = 'accounts/settings.html'

    def dispatch(self, *args, **kwargs):
        self.user = self.request.user
        if not is_password_usable(self.user.password):
            self.password_text = _('No password set.')
            self.password_link_text = _('Password set')
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.user

    def form_valid(self, form):
        messages.success(self.request, _('Settings updated successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_text'] = self.password_text
        context['password_link_text'] = self.password_link_text
        return context


@login_required
@sensitive_post_parameters
class PasswordChangeView(auth_views.PasswordChangeView):
    success_url = reverse_lazy('accounts:settings')
    template_name = 'accounts/password_change.html'

    def dispatch(self, *args, **kwargs):
        self.user = self.request.user
        if not is_password_usable(self.user.password):
            self.form_class = PasswordCreationForm
            self.title = _('Password set')
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _('Password changed successfully.'))
        return super().form_valid(form)


class PasswordResetView(auth_views.PasswordResetView):
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    template_name = 'accounts/password_reset.html'


INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    success_url = reverse_lazy('accounts:password_reset_complete')
    template_name = 'accounts/password_reset_confirm.html'


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class LoginView(auth_views.LoginView):
    authentication_form = AuthenticationForm
    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('accounts:login')


class SignupView(generic.FormView):
    form_class = SignupForm
    success_url = reverse_lazy('accounts:signup_complete')
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class SignupCompleteView(generic.TemplateView):
    template_name = 'accounts/signup_complete.html'


INTERNAL_VERIFICATION_SESSION_TOKEN = '_verification_token'


class VerificationView(generic.TemplateView):
    complete_url_token = 'complete'
    error_url = reverse_lazy('accounts:verification_again')
    post_verification_login = True
    post_verification_login_backend = 'accounts.backends.ModelBackend'
    template_name = 'accounts/verification.html'
    token_generator = default_token_generator

    def dispatch(self, *args, **kwargs):
        assert 'uidb64' in kwargs and 'token' in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs['uidb64'])

        if self.user is not None:
            token = kwargs['token']
            if token == self.complete_url_token:
                session_token = self.request.session.get(INTERNAL_VERIFICATION_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    self.request.session[INTERNAL_VERIFICATION_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, self.complete_url_token)
                    return HttpResponseRedirect(redirect_url)

        return HttpResponseRedirect(self.error_url)

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist, ValidationError):
            user = None
        return user

    def get(self, request, *args, **kwargs):
        if not self.user.is_active and self.user.date_verified == None:
            self.user.is_active = True
            self.user.date_verified = timezone.now()
            self.user.save()
            if self.post_verification_login:
                auth_login(self.request, self.user, self.post_verification_login_backend)
        return super().get(request, *args, **kwargs)


class VerificationAgainView(generic.FormView):
    form_class = VerificationAgainForm
    success_url = reverse_lazy('accounts:verification_sent')
    template_name = 'accounts/verification_again.html'

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class VerificationSentView(generic.TemplateView):
    template_name = 'accounts/verification_sent.html'
