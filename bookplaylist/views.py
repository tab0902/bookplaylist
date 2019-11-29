import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required as login_required_
from django.shortcuts import redirect
from django.templatetags.static import static
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


class TemplateContextMixin:
    page_title = _('Share Book Playlists on your SNS.')
    page_description = \
        'BooxMixは、気軽に本を複数冊まとめてプレイリストを作成し、SNSでシェアできるウェブサービスです。誰もが本屋の書店員さんのようにおすすめ本を選びTwitterで共有できます。本選びに悩む人も、リストから新しい本を発見できます。'
    og_type = 'article'
    og_image = static('img/hero-sp.jpg')
    og_site_name = 'BooxMix'
    twitter_card = 'summary_large_image'
    twitter_site = '@BooxMix'

    def dispatch(self, *args, **kwargs):
        self.og_url = '{}://{}'.format(self.request.scheme, self.request.get_host())
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': self.page_title,
            'page_description': self.page_description,
            'og_type': self.og_type,
            'og_url': self.og_url,
            'og_image': self.og_image,
            'og_site_name': self.og_site_name,
            'twitter_card': self.twitter_card,
            'twitter_site': self.twitter_site,
        })
        return context

    def get_full_absolute_url(self, obj):
        return '{}://{}{}'.format(self.request.scheme, self.request.get_host(), obj.get_absolute_url())


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
