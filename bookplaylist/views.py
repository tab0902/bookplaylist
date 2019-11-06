import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required as login_required_
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.decorators.debug import sensitive_post_parameters as sensitive_post_parameters_

from main.models import Playlist

login_required = method_decorator(login_required_, name='dispatch')
sensitive_post_parameters = method_decorator(sensitive_post_parameters_(), name='dispatch')


class OwnerOnlyMixin:

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'get_object'):
            obj = self.get_object()
        else:
            obj = Playlist.objects.filter(pk=self.kwargs.get('pk')).first()
        if obj.user != request.user:
            messages.warning(request, _('You don\'t have permission to access the page.'))
            if 'category' not in self.kwargs:
                self.kwargs['category'] = obj.category.slug
            return redirect('main:playlist_detail', **self.kwargs)
        return super().dispatch(request, *args, **kwargs)


class SearchFormView(generic.FormView):
    param = {'q': ''}

    def _format_query(self, raw_query):
        return [x for x in list(dict.fromkeys(re.split('[\s　]', raw_query))) if x != '']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['q'] = self.request.GET.get('q') or ''
        return kwargs

    def form_valid(self, form):
        self.param['q'] = form.cleaned_data['q']
        return super().form_valid(form)

    def get_success_url(self):
        return super().get_success_url() + '?{}'.format(urlencode(self.param))
