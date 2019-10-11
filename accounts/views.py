from django.contrib import messages
from django.contrib.auth import (
    get_user_model, login as auth_login, views as auth_views
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    SignupForm, VerificationAgainForm
)

from .models import User

UserModel = get_user_model()

# Create your views here.


class ContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


@method_decorator(login_required, name='dispatch')
class ProfileView(ContextMixin, generic.TemplateView):
    template_name = 'accounts/profile.html'
    title = _('Profile')


@method_decorator(login_required, name='dispatch')
class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, _('Password changed successfully.'))
        return super().form_valid(form)


class LoginView(ContextMixin, auth_views.LoginView):
    template_name = 'accounts/login.html'
    title = _('Log in')


class LogoutView(ContextMixin, auth_views.LogoutView):
    next_page = reverse_lazy('accounts:login')


class SignupView(ContextMixin, generic.FormView):
    form_class = SignupForm
    success_url = reverse_lazy('accounts:signup_complete')
    template_name = 'accounts/signup.html'
    title = _('Sign up')

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class SignupCompleteView(ContextMixin, generic.TemplateView):
    template_name = 'accounts/signup_complete.html'
    title = _('Sign up complete')


INTERNAL_VERIFICATION_SESSION_TOKEN = '_verification_token'


class VerificationView(ContextMixin, generic.TemplateView):
    complete_url_token = 'complete'
    error_url = reverse_lazy('accounts:verification_again')
    post_verification_login = True
    post_verification_login_backend = 'accounts.backends.ModelBackend'
    template_name = 'accounts/verification.html'
    title = _('Verification complete')
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


class VerificationAgainView(ContextMixin, generic.FormView):
    form_class = VerificationAgainForm
    success_url = reverse_lazy('accounts:verification_sent')
    template_name = 'accounts/verification_again.html'
    title = _('Verification failed')

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class VerificationAgainSentView(ContextMixin, generic.TemplateView):
    template_name = 'accounts/verification_sent.html'
    title = _('Email for verification sent')
