import re
from functools import reduce

from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import PlaylistSearchForm
from .models import Playlist
from bookplaylist.views import ContextMixin

# Create your views here.


class IndexView(ContextMixin, generic.FormView):
    form_class = PlaylistSearchForm
    success_url = reverse_lazy('main:playlist')
    template_name = 'main/index.html'
    title = _('TOP')

    def form_valid(self, form):
        self.success_url += '?q={}'.format(form.cleaned_data['query'])
        return super().form_valid(form)


class PlaylistView(ContextMixin, generic.FormView):
    form_class = PlaylistSearchForm
    success_url = reverse_lazy('main:playlist')
    template_name = 'main/playlist/list.html'
    title = _('Playlist list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queries = self.request.GET.get('q')
        if queries:
            queries = re.split('[\s　]', queries)
            queries = [x for x in list(dict.fromkeys(queries)) if x != '']
            conditions = [Q(title__icontains=x) for x in queries]\
                       + [Q(description__icontains=x) for x in queries]\
                       + [Q(books__title__icontains=x) for x in queries]\
                       + [Q(books__title_collation_key__icontains=x) for x in queries]\
                       + [Q(books__author__icontains=x) for x in queries]
            conditions = reduce(lambda x, y: x | y, conditions)
            playlists = Playlist.objects.filter(conditions)
        else:
            playlists = Playlist.objects.all()
        context['playlists'] = playlists
        return context

    def form_valid(self, form):
        self.success_url += '?q={}'.format(form.cleaned_data['query'])
        return super().form_valid(form)
