from django.views import generic
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from .forms import (
    SignupForm,
)

from .models import User

# Create your views here.


class SignupView(generic.FormView):
    extra_email_context = None
    form_class = SignupForm
    model = User
    success_url = reverse_lazy('accounts:signup_complete')
    template_name = 'accounts/signup.html'
    title = _('Signup')

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        return super().form_valid(form)


class SignupCompleteView(generic.TemplateView):
    template_name = 'accounts/signup_complete.html'


class VerificationView(generic.TemplateView):
    template_name = 'accounts/verification.html'
