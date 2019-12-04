from django.contrib import messages
from django.contrib.auth import (
    get_user_model, login as auth_login, logout as auth_logout, views as auth_views,
)
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import (
    get_object_or_404, redirect, render,
)
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    AuthenticationForm, DeacrivateForm, PasswordCreationForm, SignupForm, UserProfileForm, UserSettingsForm, VerificationAgainForm,
)
from bookplaylist.views import (
    TemplateContextMixin, login_required, sensitive_post_parameters,
)

# Create your views here.


UserModel = get_user_model()


@login_required
class IndexView(TemplateContextMixin, generic.TemplateView):
    page_title = _('My page')
    page_description = \
        'BooxMixのマイページでは、今までに自分が作成した本のプレイリストの一覧をチェックできます。何かシェアしたいことが見つかったときは、おすすめしたい本をまとめて新たにプレイリストを作成しましょう。'
    template_name = 'accounts/index.html'


@login_required
class SettingsView(TemplateContextMixin, generic.UpdateView):
    form_class = UserSettingsForm
    page_title = _('Settings')
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
class PasswordChangeView(TemplateContextMixin, auth_views.PasswordChangeView):
    page_title = _('Password change')
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


class ProfileView(TemplateContextMixin, generic.UpdateView):
    form_class = UserProfileForm
    model = UserModel
    template_name = 'accounts/profile.html'

    def get_object(self, queryset=None):
        return get_object_or_404(UserModel, username=self.kwargs.get('username'))

    def form_valid(self, form):
        if self.request.user != self.get_object():
            messages.warning(self.request, _('You don\'t have permission to update other user\'s profile.'))
            return redirect('accounts/profile.html', **self.kwargs)
        messages.success(self.request, _('Comment updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        self.success_url = self.request.path
        return super().get_success_url()

    def get_context_data(self, **kwargs):
        username = self.object.username
        self.page_title = _('%(username)s\'s profile') % {'username': username}
        self.page_description = \
            self.object.comment or \
            ''
        self.og_url = '{}://{}{}'.format(self.request.scheme, self.request.get_host(), self.request.path)
        return super().get_context_data(**kwargs)


class PasswordResetView(TemplateContextMixin, auth_views.PasswordResetView):
    email_template_name = 'accounts/password_reset_email.html'
    page_title = _('Password reset')
    success_url = reverse_lazy('accounts:password_reset_done')
    template_name = 'accounts/password_reset.html'


INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


class PasswordResetDoneView(TemplateContextMixin, auth_views.PasswordResetDoneView):
    page_title = _('Email to reset password sent')
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(TemplateContextMixin, auth_views.PasswordResetConfirmView):
    page_title = _('Password reset')
    success_url = reverse_lazy('accounts:password_reset_complete')
    template_name = 'accounts/password_reset_confirm.html'

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel.all_objects_without_deleted.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist, ValidationError):
            user = None
        return user


class PasswordResetCompleteView(TemplateContextMixin, auth_views.PasswordResetCompleteView):
    page_title = _('Password reset complete')
    template_name = 'accounts/password_reset_complete.html'


class LoginView(TemplateContextMixin, auth_views.LoginView):
    authentication_form = AuthenticationForm
    page_title = _('Log in')
    page_description = \
        'BooxMixは、気軽に本を複数冊まとめてプレイリストを作成し、SNSでシェアできるウェブサービスです。誰もが本屋の書店員さんのようにおすすめ本を選びTwitterで共有できます。ログインしてプレイリストを作り、友達に共有しましょう。'
    template_name = 'accounts/login.html'


class LogoutView(TemplateContextMixin, auth_views.LogoutView):
    next_page = reverse_lazy('accounts:login')


class SignupView(TemplateContextMixin, generic.FormView):
    form_class = SignupForm
    page_title = _('Sign up')
    page_description = \
        'BooxMixは、気軽に本を複数冊まとめてプレイリストを作成し、SNSでシェアできるウェブサービスです。誰もが本屋の書店員さんのようにおすすめ本を選びTwitterで共有できます。あなたも登録してプレイリストを作成しませんか。'
    success_url = reverse_lazy('accounts:signup_complete')
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class SignupCompleteView(TemplateContextMixin, generic.TemplateView):
    page_title = _('Sign up complete')
    template_name = 'accounts/signup_complete.html'


INTERNAL_VERIFICATION_SESSION_TOKEN = '_verification_token'


class VerificationView(TemplateContextMixin, generic.TemplateView):
    complete_url_token = 'complete'
    error_url = reverse_lazy('accounts:verification_again')
    page_title = _('Verification complete')
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
            user = UserModel.all_objects_without_deleted.get(pk=uid)
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


class VerificationAgainView(TemplateContextMixin, generic.FormView):
    form_class = VerificationAgainForm
    page_title = _('Verification failed')
    success_url = reverse_lazy('accounts:verification_sent')
    template_name = 'accounts/verification_again.html'

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class VerificationSentView(TemplateContextMixin, generic.TemplateView):
    page_title = _('Email for verification sent')
    template_name = 'accounts/verification_sent.html'


@login_required
class DeacrivateView(TemplateContextMixin, generic.UpdateView):
    form_class = DeacrivateForm
    model = UserModel
    page_title = _('Deactivate your account')
    success_url = reverse_lazy('accounts:deactivate_complete')
    template_name = 'accounts/deactivate.html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.is_active = False
        instance.save()
        auth_logout(self.request)
        return super().form_valid(form)


class DeacrivateCompleteView(TemplateContextMixin, generic.TemplateView):
    page_title = _('Your account deactivated')
    template_name = 'accounts/deactivate_complete.html'
