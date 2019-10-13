import re
from functools import reduce

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    PlaylistForm, PlaylistSearchForm,
)
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


class PlaylistCreateView(ContextMixin, generic.CreateView):
    form_class = PlaylistForm
    model = Playlist
    success_url = reverse_lazy('main:playlist_create_complete')
    template_name = 'main/playlist/create.html'
    title = _('Create playlist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class PlaylistCreateCompleteView(ContextMixin, generic.TemplateView):
    template_name = 'main/playlist/create_complete.html'
    title = _('Playlist created')


class PlaylistUpdateView(ContextMixin, generic.UpdateView):
    form_class = PlaylistForm
    model = Playlist
    template_name = 'main/playlist/update.html'
    title = _('Update playlist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('Playlist updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('main:playlist_detail', args=(self.kwargs.get('pk'),))


class PlaylistDeleteView(ContextMixin, generic.DeleteView):
    model = Playlist
    success_url = reverse_lazy('accounts:index')
    template_name = 'main/playlist/delete.html'
    title = _('Delete playlist')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Playlist deleted successfully.'))
        return super().delete(request, *args, **kwargs)
