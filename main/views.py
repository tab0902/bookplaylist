import re
from functools import reduce

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    PlaylistForm, SearchForm,
)
from .models import (
    Book, Playlist,
)
from bookplaylist.views import (
    ContextMixin, SearchFormView, login_required,
)

# Create your views here.


class IndexView(ContextMixin, SearchFormView):
    form_class = SearchForm
    success_url = reverse_lazy('main:playlist')
    template_name = 'main/index.html'
    title = _('TOP')


class PlaylistView(ContextMixin, SearchFormView):
    form_class = SearchForm
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


SESSION_KEY_PREFIX = 'books_'
MODE_CREATE = 'create'
MODE_UPDATE = 'update'


class BookMixin:
    mode = None

    def _get_key_name(self):
        return SESSION_KEY_PREFIX + self.mode


@login_required
class PlaylistCreateView(ContextMixin, BookMixin, generic.CreateView):
    form_class = PlaylistForm
    mode = MODE_CREATE
    model = Playlist
    success_url = reverse_lazy('main:playlist_create_complete')
    template_name = 'main/playlist/create.html'
    title = _('Create playlist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        key = self._get_key_name()
        if not request.GET.get('continue') and key in request.session:
            del request.session[key]
        return super().get(request, *args, **kwargs)


@login_required
class PlaylistUpdateView(ContextMixin, BookMixin, generic.UpdateView):
    form_class = PlaylistForm
    mode = MODE_UPDATE
    model = Playlist
    template_name = 'main/playlist/update.html'
    title = _('Update playlist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        key = self._get_key_name()
        if not request.GET.get('continue') and key in request.session:
            del request.session[key]
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, _('Playlist updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('main:playlist_detail', args=(self.kwargs.get('pk'),))


@login_required
class BasePlaylistBookView(ContextMixin, BookMixin, SearchFormView):
    form_class = SearchForm
    success_url = None
    template_name = 'main/playlist/books.html'
    title = _('Search Book')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            q_list = re.split('\s', query)
            conditions = [Q(title__icontains=q) for q in q_list]\
                       + [Q(title_collation_key__icontains=q) for q in q_list]\
                       + [Q(author__icontains=q) for q in q_list]
            conditions = reduce(lambda x, y: x | y, conditions)
            books = Book.objects.filter(conditions).order_by('pubdate')
        else:
            books = None
        context['books'] = books
        context['books_in_session'] = self.request.session.get(self._get_key_name())
        context['mode'] = self.mode
        return context


class PlaylistCreateBookView(BasePlaylistBookView):
    mode = MODE_CREATE
    success_url = reverse_lazy('main:playlist_create_book')


class PlaylistUpdateBookView(BasePlaylistBookView):
    mode = MODE_UPDATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs.get('pk')
        return context

    def get_success_url(self):
        self.success_url = reverse_lazy('main:playlist_update_book', args=(self.kwargs.get('pk'),))
        return super().get_success_url()


@login_required
class BasePlaylistBookStoreView(BookMixin, generic.RedirectView):
    url = None

    def dispatch(self, *args, **kwargs):
        book = str(self.kwargs.get('book'))
        session = self.request.session
        key = self._get_key_name()
        if key in session and book not in session.get('key'):
            session[key] += [book]
        else:
            session[key] = [book]
        return super().dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        self.url += '?continue=True'
        return super().get_redirect_url(*args, **kwargs)


@login_required
class PlaylistCreateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_CREATE
    url = reverse_lazy('main:playlist_create')


@login_required
class PlaylistUpdateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_UPDATE

    def get_redirect_url(self, *args, **kwargs):
        self.url = reverse_lazy('main:playlist_update', args=(self.kwargs.get('pk'),))
        return super().get_redirect_url(*args, **kwargs)


@login_required
class PlaylistCreateCompleteView(ContextMixin, generic.TemplateView):
    template_name = 'main/playlist/create_complete.html'
    title = _('Playlist created successfully.')


@login_required
class PlaylistDeleteView(ContextMixin, generic.DeleteView):
    model = Playlist
    success_url = reverse_lazy('accounts:index')
    template_name = 'main/playlist/delete.html'
    title = _('Delete playlist')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Playlist deleted successfully.'))
        return super().delete(request, *args, **kwargs)
