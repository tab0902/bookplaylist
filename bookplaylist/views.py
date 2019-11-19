import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required as login_required_
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.csrf import csrf_protect as csrf_protect_
from django.views.decorators.debug import sensitive_post_parameters as sensitive_post_parameters_

from main.models import (
    Playlist, Provider,
)

csrf_protect = method_decorator(csrf_protect_, name='dispatch')
login_required = method_decorator(login_required_, name='dispatch')
sensitive_post_parameters = method_decorator(sensitive_post_parameters_(), name='dispatch')


class OwnerOnlyMixin:

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'object'):
            pass
        elif hasattr(self, 'get_object'):
            self.object = self.get_object()
        else:
            self.object = Playlist.objects.filter(pk=self.kwargs.get('pk')).first()
        if self.object.user != request.user:
            messages.warning(request, _('You don\'t have permission to access the page.'))
            return redirect('main:playlist_detail', **self.kwargs)
        return super().dispatch(request, *args, **kwargs)


class SearchFormView(generic.FormView):
    param = {'q': ''}

    def _format_query(self, raw_query):
        return [x for x in list(dict.fromkeys(re.split(r'[\s　]', raw_query))) if x != '']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['q'] = self.request.GET.get('q') or ''
        return kwargs

    def form_valid(self, form):
        self.param['q'] = form.cleaned_data['q']
        return super().form_valid(form)

    def get_success_url(self):
        return super().get_success_url() + '?{}'.format(urlencode(self.param))
