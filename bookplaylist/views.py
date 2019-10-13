import re

from django.utils.http import urlencode
from django.views import generic


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

    def _encode_query(self, raw_query):
        query_list = [x for x in list(dict.fromkeys(re.split('[\s　]', raw_query))) if x != '']
        query = urlencode({'q': ' '.join(query_list)})
        return query

    def form_valid(self, form):
        query = self._encode_query(form.cleaned_data['q'])
        self.success_url += '?{}'.format(query)
        return super().form_valid(form)