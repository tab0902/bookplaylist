from functools import reduce
from itertools import chain

from django import forms
from django.contrib import messages
from django.db.models import (
    Count, Q,
)
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, render_to_response
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    BookSearchForm, PlaylistBookFormSet, PlaylistForm, PlaylistSearchForm,
)
from .models import (
    Book, Playlist, Theme,
)
from bookplaylist.views import (
    OwnerOnlyMixin, SearchFormView, login_required,
)

# Create your views here.


class PlaylistSearchFormView(SearchFormView):
    form_class = PlaylistSearchForm
    success_url = reverse_lazy('main:playlist')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['theme'] = self.request.GET.get('theme') or None
        return kwargs

    def form_valid(self, form):
        theme = form.cleaned_data['theme']
        self.param['theme'] = theme.slug if theme else ''
        return super().form_valid(form)


class IndexView(PlaylistSearchFormView):
    template_name = 'main/index.html'


class PlaylistView(generic.list.BaseListView, PlaylistSearchFormView):
    context_object_name = 'playlists'
    model = Playlist
    template_name = 'main/playlist/list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        theme = self.request.GET.get('theme')
        condition_lists = []
        condition_dict = {}
        if theme:
            condition_dict['theme__slug'] = theme
        if query:
            q_list = self._format_query(query)
            condition_lists.append([
                  Q(title__iexact=q)\
                | Q(description__iexact=q)\
                | Q(books__title__iexact=q)\
                | Q(books__title_collation_key__iexact=q)\
                | Q(books__author__iexact=q)
                for q in q_list
            ])
            condition_lists.append([
                  Q(title__icontains=q)\
                | Q(description__icontains=q)\
                | Q(books__title__icontains=q)\
                | Q(books__title_collation_key__icontains=q)\
                | Q(books__author__icontains=q)
                for q in q_list
            ])
            queryset = Playlist.objects.none()
            for condition_list_ in condition_lists:
                queryset = chain(queryset, Playlist.objects.filter(*condition_list_, **condition_dict))
            queryset = list(dict.fromkeys(queryset))
        else:
            condition_list = []
            queryset = Playlist.objects.filter(*condition_list, **condition_dict).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['params'] = {
            'q': self.request.GET.get('q'),
            'theme': self.request.GET.get('theme'),
        }
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

    def form_invalid(self, form, instance):
        formset = PlaylistBookFormSet(self.request.POST, instance=instance, form_kwargs={'request': self.request})
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


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
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        instance.save()
        formset.save()
        for key in (SESSION_KEY_FORM, SESSION_KEY_BOOK,):
            if SESSION_KEY_FORM in self.request.session:
                del self.request.session[key]
        return super().form_valid(form)

    def form_invalid(self, form):
        instance = None
        return super().form_invalid(form, instance)

    def get_success_url(self):
        self.success_url = reverse_lazy('main:playlist_create_complete', kwargs={'pk': str(self.object.pk)})
        return super().get_success_url()


@login_required
class PlaylistUpdateView(OwnerOnlyMixin, BasePlaylistView, generic.UpdateView):
    mode = MODE_UPDATE
    template_name = 'main/playlist/update.html'

    def get(self, request, *args, **kwargs):
        initial = {
            'form': None,
            'book': [
                {
                    'id': str(x.book.id),
                    'isbn': str(x.book.isbn),
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
            return redirect('main:playlist_{}_book'.format(self.mode), **self.kwargs)
        instance = form.save(commit=False)
        formset = PlaylistBookFormSet(self.request.POST, instance=instance, form_kwargs={'request': self.request})
        if not len(formset.forms) - len(formset.deleted_forms):
            messages.error(self.request, _('You have to add at least one book to your playlist.'))
            self.request.session[SESSION_KEY_FORM] = self.request.POST
            url = reverse_lazy('main:playlist_{}'.format(self.mode), kwargs=self.kwargs) + '?{}=True'.format(GET_KEY_CONTINUE)
            return HttpResponseRedirect(url)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        instance.save()
        formset.save()
        for key in (SESSION_KEY_FORM, SESSION_KEY_BOOK,):
            if SESSION_KEY_FORM in self.request.session:
                del self.request.session[key]
        messages.success(self.request, _('Playlist updated successfully.'))
        return super().form_valid(form)

    def form_invalid(self, form):
        instance = self.get_object()
        return super().form_invalid(form, instance)

    def get_success_url(self):
        self.success_url = reverse_lazy('main:playlist_detail', kwargs=self.kwargs)
        return super().get_success_url()


@login_required
class BasePlaylistBookView(generic.list.BaseListView, SearchFormView):
    context_object_name = 'books'
    form_class = BookSearchForm
    model = Book
    paginate_by = 24
    success_url = None
    template_name = 'main/playlist/book.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            q_list = self._format_query(query)
            condition_lists = []
            condition_lists.append([Q(title__iexact=q) | Q(title_collation_key__iexact=q) | Q(author__iexact=q) for q in q_list])
            condition_lists.append([Q(title__icontains=q) | Q(title_collation_key__icontains=q) | Q(author__icontains=q) for q in q_list])
            queryset = Playlist.objects.none()
            for condition_list in condition_lists:
                queryset = chain(
                    queryset,
                    Book.objects.filter(*condition_list).annotate(Count('playlists')).order_by('-playlists__count', '-pubdate').distinct()
                )
            queryset = list(dict.fromkeys(queryset))
        else:
            queryset = Book.objects.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books_in_session'] = [x['isbn'] for x in self.request.session.get(SESSION_KEY_BOOK)] if SESSION_KEY_BOOK in self.request.session else []
        context['mode'] = self.mode
        context['params'] = {
            'q': self.request.GET.get('q'),
        }
        return context

    def get_success_url(self):
        self.success_url = reverse_lazy('main:playlist_{}_book'.format(self.mode), kwargs=self.kwargs)
        return super().get_success_url()


class PlaylistCreateBookView(BasePlaylistBookView):
    mode = MODE_CREATE


class PlaylistUpdateBookView(OwnerOnlyMixin, BasePlaylistBookView):
    mode = MODE_UPDATE


@login_required
class BasePlaylistBookStoreView(generic.RedirectView):
    url = None

    def dispatch(self, *args, **kwargs):
        form_data = self.request.session.get(SESSION_KEY_FORM)
        book_data = self.request.session.get(SESSION_KEY_BOOK)
        if not form_data or not SESSION_KEY_BOOK in self.request.session:
            messages.warning(self.request, _('Session timeout. Please retry from the beginning.'))
            return redirect('main:playlist_{}'.format(self.mode), **self.kwargs)
        book_obj = Book.objects.get(pk=str(self.kwargs.get('book')))
        book_json = {
            'id': str(book_obj.id),
            'isbn': str(book_obj.isbn),
            'title': book_obj.title,
            'author': book_obj.author,
            'cover': book_obj.cover,
        }
        if book_json not in self.request.session.get(SESSION_KEY_BOOK):
            self.request.session[SESSION_KEY_BOOK] += [book_json]
            book_num = len(self.request.session[SESSION_KEY_BOOK])
            self.request.session[SESSION_KEY_FORM]['playlistbook_set-{}-book'.format(book_num-1)] = book_json['isbn']
            self.request.session[SESSION_KEY_FORM]['playlistbook_set-TOTAL_FORMS'] = str(int(self.request.session[SESSION_KEY_FORM]['playlistbook_set-TOTAL_FORMS']) + 1)
        return super().dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        del self.kwargs['book']
        self.url = reverse_lazy('main:playlist_{}'.format(self.mode), kwargs=self.kwargs) + '?{}=True'.format(GET_KEY_CONTINUE)
        return super().get_redirect_url(*args, **kwargs)


class PlaylistCreateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_CREATE


class PlaylistUpdateBookStoreView(OwnerOnlyMixin, BasePlaylistBookStoreView):
    mode = MODE_UPDATE


@login_required
class PlaylistCreateCompleteView(OwnerOnlyMixin, generic.DetailView):
    model = Playlist
    template_name = 'main/playlist/create_complete.html'


@login_required
class PlaylistDeleteView(OwnerOnlyMixin, generic.DeleteView):
    model = Playlist
    success_url = reverse_lazy('accounts:index')
    template_name = 'main/playlist/delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Playlist deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class TermsView(generic.TemplateView):
    template_name = 'main/terms.html'


class PrivacyView(generic.TemplateView):
    template_name = 'main/privacy.html'
