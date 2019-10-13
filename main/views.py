import re
from functools import reduce

from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import PlaylistSearchForm
from .models import Playlist
from bookplaylist.views import (
    ContextMixin, SearchFormView,
)

# Create your views here.


class IndexView(ContextMixin, SearchFormView):
    form_class = PlaylistSearchForm
    success_url = reverse_lazy('main:playlist')
    template_name = 'main/index.html'
    title = _('TOP')


class PlaylistView(ContextMixin, SearchFormView):
    form_class = PlaylistSearchForm
    success_url = reverse_lazy('main:playlist')
    template_name = 'main/playlist/list.html'
    title = _('Playlist list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            q_list = re.split('\s', query)
            conditions = [Q(title__icontains=q) for q in q_list]\
                       + [Q(description__icontains=q) for q in q_list]\
                       + [Q(books__title__icontains=q) for q in q_list]\
                       + [Q(books__title_collation_key__icontains=q) for q in q_list]\
                       + [Q(books__author__icontains=q) for q in q_list]
            conditions = reduce(lambda x, y: x | y, conditions)
            playlists = Playlist.objects.filter(conditions)
        else:
            playlists = Playlist.objects.all()
        context['playlists'] = playlists
        return context


class PlaylistDetailView(ContextMixin, generic.DetailView):
    model = Playlist
    template_name = 'main/playlist/detail.html'
    title = None

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=None)
        self.title = obj.title
        return obj
