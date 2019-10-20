import re

from django.contrib.auth.decorators import login_required as login_required_
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.views import generic
from django.views.decorators.debug import sensitive_post_parameters as sensitive_post_parameters_

login_required = method_decorator(login_required_, name='dispatch')
sensitive_post_parameters = method_decorator(sensitive_post_parameters_(), name='dispatch')


class ContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


class SearchFormView(generic.FormView):
    query = {}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['q'] = self.request.GET.get('q') or ''
        return kwargs

    def _format_query(self, raw_query):
        query_list = [x for x in list(dict.fromkeys(re.split('[\s　]', raw_query))) if x != '']
        query = ' '.join(query_list)
        return query

    def form_valid(self, form):
        self.query['q'] = self._format_query(form.cleaned_data['q'])
        return super().form_valid(form)

    def get_success_url(self):
        return super().get_success_url() + '?{}'.format(urlencode(self.query))
