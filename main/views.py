import re
from functools import reduce
from itertools import zip_longest

from django import forms
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, render_to_response
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    PlaylistForm, PlaylistBookFormSet, SearchForm,
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


MODE_CREATE = 'create'
MODE_UPDATE = 'update'
GET_KEY_CONTINUE = 'continue'
POST_KEY_SEARCH = 'search'
POST_KEY_ADD_BOOK = 'add_book'
SESSION_KEY_FORM = 'playlist_form_data'
SESSION_KEY_FORMSET = 'playlist_formset_data'
SESSION_KEY_BOOK = 'playlist_book_data'


class BasePlaylistView(ContextMixin):
    form_class = PlaylistForm
    model = Playlist

    def get(self, request, initial, *args, **kwargs):
        if not request.GET.get(GET_KEY_CONTINUE):
            request.session[SESSION_KEY_FORM] = initial['form']
            request.session[SESSION_KEY_BOOK] = initial['book']
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        form_data = self.request.session.get(SESSION_KEY_FORM)
        if form_data:
            kwargs['initial'] = form_data
        return kwargs

    def get_context_data(self, instance, **kwargs):
        context = super().get_context_data(**kwargs)
        form_data = self.request.session.get(SESSION_KEY_FORM)
        book_data = self.request.session.get(SESSION_KEY_BOOK)
        formset = kwargs.get('formset') or PlaylistBookFormSet(form_data, instance=instance, form_kwargs={'request': self.request})
        context['formset'] = formset
        context['book_formset'] = zip(formset or [], book_data or [])
        return context


@login_required
class PlaylistCreateView(BasePlaylistView, generic.CreateView):
    mode = MODE_CREATE
    success_url = reverse_lazy('main:playlist_create_complete')
    template_name = 'main/playlist/create.html'
    title = _('Create playlist')

    def get(self, request, *args, **kwargs):
        initial = {
            'form': None,
            'book': [],
        }
        return super().get(request, initial, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(instance=None, **kwargs)

    def form_valid(self, form):
        if POST_KEY_ADD_BOOK in self.request.POST:
            self.request.POST = self.request.POST.copy()
            del self.request.POST[POST_KEY_ADD_BOOK]
            self.request.session[SESSION_KEY_FORM] = self.request.POST
            return redirect('main:playlist_{}_book'.format(self.mode))
        instance = form.save(commit=False)
        formset = PlaylistBookFormSet(self.request.POST, instance=instance, form_kwargs={'request': self.request})
        if not len(formset.forms) - len(formset.deleted_forms):
            messages.error(self.request, _('You have to add at least one book to your playlist.'.format(self.mode)))
            url = reverse_lazy('main:playlist_{}'.format(self.mode)) + '?{}=True'.format(GET_KEY_CONTINUE)
            return HttpResponseRedirect(url)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))
        instance.save()
        formset.save()
        del self.request.session[SESSION_KEY_FORM]
        del self.request.session[SESSION_KEY_BOOK]
        return super().form_valid(form)


@login_required
class PlaylistUpdateView(BasePlaylistView, generic.UpdateView):
    mode = MODE_UPDATE
    template_name = 'main/playlist/update.html'
    title = _('Update playlist')

    def get(self, request, *args, **kwargs):
        initial = {
            'form': None,
            'book': [
                {
                    'id': str(x.book.id),
                    'title': x.book.title,
                    'author': x.book.author,
                    'cover': x.book.cover,
                }
                for x in self.get_object().playlistbook_set.all()
            ]
        }
        return super().get(request, initial, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(instance=self.get_object(), **kwargs)

    def form_valid(self, form):
        if POST_KEY_ADD_BOOK in self.request.POST:
            self.request.POST = self.request.POST.copy()
            del self.request.POST[POST_KEY_ADD_BOOK]
            self.request.session[SESSION_KEY_FORM] = self.request.POST
            pk = str(self.kwargs.get('pk'))
            return redirect('main:playlist_{}_book'.format(self.mode), pk=pk)
        instance = form.save(commit=False)
        formset = PlaylistBookFormSet(self.request.POST, instance=instance, form_kwargs={'request': self.request})
        if not len(formset.forms) - len(formset.deleted_forms):
            messages.error(self.request, _('You have to add at least one book to your playlist.'.format(self.mode)))
            args = (str(self.kwargs.get('pk')),)
            url = reverse_lazy('main:playlist_{}'.format(self.mode), args=args) + '?{}=True'.format(GET_KEY_CONTINUE)
            return HttpResponseRedirect(url)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))
        instance.save()
        formset.save()
        del self.request.session[SESSION_KEY_FORM]
        del self.request.session[SESSION_KEY_BOOK]
        messages.success(self.request, _('Playlist updated successfully.'))
        return super().form_valid(form)

    def get_success_url(self):
        args = (str(self.kwargs.get('pk')),)
        self.success_url = reverse_lazy('main:playlist_detail', args=args)
        return super().get_success_url()


@login_required
class BasePlaylistBookView(ContextMixin, SearchFormView):
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
        context['books_in_session'] = [x['id'] for x in self.request.session.get(SESSION_KEY_BOOK)] if SESSION_KEY_BOOK in self.request.session else []
        context['mode'] = self.mode
        return context

    def get_success_url(self):
        args = (str(self.kwargs.get('pk')),) if self.kwargs.get('pk') else tuple()
        self.success_url = reverse_lazy('main:playlist_{}_book'.format(self.mode), args=args)
        return super().get_success_url()


class PlaylistCreateBookView(BasePlaylistBookView):
    mode = MODE_CREATE


class PlaylistUpdateBookView(BasePlaylistBookView):
    mode = MODE_UPDATE


@login_required
class BasePlaylistBookStoreView(generic.RedirectView):
    url = None

    def dispatch(self, *args, **kwargs):
        self.request.session[SESSION_KEY_FORM] = None
        form_data = self.request.session.get(SESSION_KEY_FORM)
        book_data = self.request.session.get(SESSION_KEY_BOOK)
        if not form_data or not SESSION_KEY_BOOK in self.request.session:
            messages.warning(self.request, _('Session timeout. Please retry from the beginning.'))
            return redirect(self.get_redirect_url())
        book_obj = Book.objects.get(pk=str(self.kwargs.get('book')))
        book_json = {
            'id': str(book_obj.id),
            'title': book_obj.title,
            'author': book_obj.author,
            'cover': book_obj.cover,
        }
        if book_json not in self.request.session.get(SESSION_KEY_BOOK):
            self.request.session[SESSION_KEY_BOOK] += [book_json]
            book_num = len(self.request.session[SESSION_KEY_BOOK])
            self.request.session[SESSION_KEY_FORM]['playlistbook_set-{}-book'.format(book_num-1)] = book_json['id']
            self.request.session[SESSION_KEY_FORM]['playlistbook_set-TOTAL_FORMS'] = str(int(self.request.session[SESSION_KEY_FORM]['playlistbook_set-TOTAL_FORMS']) + 1)
        return super().dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        args = (str(self.kwargs.get('pk')),) if self.kwargs.get('pk') else tuple()
        self.url = reverse_lazy('main:playlist_{}'.format(self.mode), args=args) + '?{}=True'.format(GET_KEY_CONTINUE)
        return super().get_redirect_url(*args, **kwargs)


class PlaylistCreateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_CREATE


class PlaylistUpdateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_UPDATE


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
