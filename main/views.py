from functools import reduce

from django import forms
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, render_to_response
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    BookSearchForm, PlaylistBookFormSet, PlaylistForm, PlaylistSearchForm,
)
from .models import (
    Book, Category, Playlist,
)
from bookplaylist.views import (
    SearchFormView, login_required,
)

# Create your views here.


class PlaylistSearchFormView(SearchFormView):
    form_class = PlaylistSearchForm
    success_url = reverse_lazy('main:playlist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['category'] = self.request.GET.get('category') or None
        return kwargs

    def form_valid(self, form):
        category = form.cleaned_data['category']
        self.param['category'] = category.slug if category else ''
        return super().form_valid(form)


class IndexView(PlaylistSearchFormView):
    template_name = 'main/index.html'


class PlaylistView(PlaylistSearchFormView):
    template_name = 'main/playlist/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        category = self.request.GET.get('category')
        condition_list = []
        condition_dict = {}
        if query:
            q_list = self._format_query(query)
            conditions = [Q(title__icontains=q) for q in q_list]\
                       + [Q(description__icontains=q) for q in q_list]\
                       + [Q(books__title__icontains=q) for q in q_list]\
                       + [Q(books__title_collation_key__icontains=q) for q in q_list]\
                       + [Q(books__author__icontains=q) for q in q_list]
            condition_list.append(reduce(lambda x, y: x | y, conditions))
        if category:
            condition_dict['category__slug'] = category
        context['playlists'] = Playlist.objects.filter(*condition_list, **condition_dict)
        context['query'] = query
        return context


class PlaylistDetailView(generic.DetailView):
    model = Playlist
    template_name = 'main/playlist/detail.html'


MODE_CREATE = 'create'
MODE_UPDATE = 'update'
GET_KEY_CONTINUE = 'continue'
POST_KEY_SEARCH = 'search'
POST_KEY_ADD_BOOK = 'add_book'
SESSION_KEY_FORM = 'playlist_form_data'
SESSION_KEY_BOOK = 'playlist_book_data'


class BasePlaylistView:
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
    template_name = 'main/playlist/create.html'

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
            messages.error(self.request, _('You have to add at least one book to your playlist.'))
            self.request.session[SESSION_KEY_FORM] = self.request.POST
            url = reverse_lazy('main:playlist_{}'.format(self.mode)) + '?{}=True'.format(GET_KEY_CONTINUE)
            return HttpResponseRedirect(url)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))
        instance.save()
        formset.save()
        del self.request.session[SESSION_KEY_FORM]
        del self.request.session[SESSION_KEY_BOOK]
        return super().form_valid(form)

    def get_success_url(self):
        args = (str(self.object.pk),)
        self.success_url = reverse_lazy('main:playlist_create_complete', args=args)
        return super().get_success_url()


@login_required
class PlaylistUpdateView(BasePlaylistView, generic.UpdateView):
    mode = MODE_UPDATE
    template_name = 'main/playlist/update.html'

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
            category = str(self.kwargs.get('category'))
            pk = str(self.kwargs.get('pk'))
            return redirect('main:playlist_{}_book'.format(self.mode), category=category, pk=pk)
        instance = form.save(commit=False)
        formset = PlaylistBookFormSet(self.request.POST, instance=instance, form_kwargs={'request': self.request})
        if not len(formset.forms) - len(formset.deleted_forms):
            messages.error(self.request, _('You have to add at least one book to your playlist.'))
            self.request.session[SESSION_KEY_FORM] = self.request.POST
            args = (str(self.kwargs.get('category')), str(self.kwargs.get('pk')),)
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
        args = (str(self.kwargs.get('category')), str(self.kwargs.get('pk')),)
        self.success_url = reverse_lazy('main:playlist_detail', args=args)
        return super().get_success_url()


@login_required
class BasePlaylistBookView(SearchFormView):
    form_class = BookSearchForm
    success_url = None
    template_name = 'main/playlist/book.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            q_list = self._format_query(query)
            conditions = [Q(title__icontains=q) for q in q_list]\
                       + [Q(title_collation_key__icontains=q) for q in q_list]\
                       + [Q(author__icontains=q) for q in q_list]
            conditions = reduce(lambda x, y: x | y, conditions)
            books = Book.objects.filter(conditions).order_by('pubdate')
        else:
            books = None
        context['books'] = books
        context['books_in_session'] = [x['id'] for x in self.request.session.get(SESSION_KEY_BOOK)] if SESSION_KEY_BOOK in self.request.session else []
        context['query'] = query
        context['mode'] = self.mode
        return context

    def get_success_url(self):
        args = (str(self.kwargs.get('category')), str(self.kwargs.get('pk')),) if self.kwargs.get('category') and self.kwargs.get('pk') else tuple()
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
        args = (str(self.kwargs.get('category')), str(self.kwargs.get('pk')),) if self.kwargs.get('category') and self.kwargs.get('pk') else tuple()
        self.url = reverse_lazy('main:playlist_{}'.format(self.mode), args=args) + '?{}=True'.format(GET_KEY_CONTINUE)
        return super().get_redirect_url(*args, **kwargs)


class PlaylistCreateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_CREATE


class PlaylistUpdateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_UPDATE


@login_required
class BasePlaylistBookDeleteView(generic.RedirectView):
    url = None

    def dispatch(self, *args, **kwargs):
        book_id = str(self.kwargs.get('book'))
        self.request.session[SESSION_KEY_BOOK] = [x for x in self.request.session[SESSION_KEY_BOOK] if x['id'] != book_id]
        return super().dispatch(*args, **kwargs)


class PlaylistCreateBookDeleteView(BasePlaylistBookDeleteView):
    mode = MODE_CREATE

    def get_redirect_url(self, *args, **kwargs):
        self.url = reverse_lazy('main:playlist_create') + '?{}=True'.format(GET_KEY_CONTINUE)
        return super().get_redirect_url(*args, **kwargs)


class PlaylistUpdateBookDeleteView(BasePlaylistBookDeleteView):
    mode = MODE_UPDATE

    def dispatch(self, *args, **kwargs):
        book_id = str(self.kwargs.get('book'))
        playlist_id = str(self.kwargs.get('pk'))
        playlist = Playlist.objects.get(pk=playlist_id)
        playlist_book = playlist.playlistbook_set.filter(book__id=book_id)
        if playlist_book:
            playlist_book.delete()
        return super().dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        args = (str(self.kwargs.get('category')), str(self.kwargs.get('pk')),) if self.kwargs.get('category') and self.kwargs.get('pk') else tuple()
        self.url = reverse_lazy('main:playlist_update', args=args) + '?{}=True'.format(GET_KEY_CONTINUE)
        return super().get_redirect_url(*args, **kwargs)


@login_required
class PlaylistCreateCompleteView(generic.DetailView):
    model = Playlist
    template_name = 'main/playlist/create_complete.html'


@login_required
class PlaylistDeleteView(generic.DeleteView):
    model = Playlist
    success_url = reverse_lazy('accounts:index')
    template_name = 'main/playlist/delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Playlist deleted successfully.'))
        return super().delete(request, *args, **kwargs)
