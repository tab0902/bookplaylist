import re
import requests
from itertools import chain

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import (
    Count, Q,
)
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError,
)
from django.shortcuts import redirect, render, render_to_response
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    BookSearchForm, ContactForm, PlaylistBookFormSet, PlaylistForm, PlaylistSearchForm,
)
from .models import (
    Book, BookData, Playlist, Theme,
)
from bookplaylist.utils import APIMixin
from bookplaylist.views import (
    OwnerOnlyMixin, SearchFormView, csrf_protect, login_required,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['themes'] = [
            (
                theme,
                Playlist.objects \
                    .annotate(Count('playlist_book')) \
                    .filter(
                        theme=theme,
                        playlist_book__count__gte=2)[:4]
            )
            for theme in Theme.objects.filter(sequence__isnull=False)
        ]
        return context


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
        context['theme'] = Theme.objects.filter(slug=self.request.GET.get('theme')).first()
        return context


class PlaylistDetailView(generic.DetailView):
    model = Playlist
    template_name = 'main/playlist/detail.html'

    def get_queryset(self):
        return super().get_queryset().select_related('theme', 'user')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        conditions = {'playlist_book__count__gte': 2}
        if self.object.theme:
            conditions['theme'] = self.object.theme
        context['other_playlists'] = Playlist.objects \
            .annotate(Count('playlist_book')) \
            .exclude(pk=self.object.pk) \
            .filter(**conditions)[:4]
        return context


MODE_CREATE = 'create'
MODE_UPDATE = 'update'
GET_KEY_CONTINUE = 'continue'
POST_KEY_SEARCH = 'search'
POST_KEY_ADD_BOOK = 'add_book'
SESSION_KEY_FORM = 'playlist_form_data'
SESSION_KEY_BOOK = 'playlist_book_data'


class BasePlaylistFormView(generic.detail.SingleObjectTemplateResponseMixin, generic.edit.ModelFormMixin, generic.edit.ProcessFormView):
    form_class = PlaylistForm
    model = Playlist

    def get(self, request, *args, **kwargs):
        if not request.GET.get(GET_KEY_CONTINUE):
            request.session[SESSION_KEY_FORM] = self.initial_form_data
            request.session[SESSION_KEY_BOOK] = self.initial_book_data
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        form_data = self.request.session.get(SESSION_KEY_FORM)
        if form_data:
            kwargs['initial'] = form_data
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_data = self.request.session.get(SESSION_KEY_FORM)
        book_data = self.request.session.get(SESSION_KEY_BOOK)
        formset = kwargs.get('formset') or PlaylistBookFormSet(form_data, instance=self.object, form_kwargs={'request': self.request})
        context['formset'] = formset
        context['book_formset'] = zip(formset or [], book_data or [])
        return context

    def form_valid(self, form):
        if POST_KEY_ADD_BOOK in self.request.POST:
            post_data = self.request.POST.copy()
            del post_data[POST_KEY_ADD_BOOK]
            self.request.session[SESSION_KEY_FORM] = post_data
            return redirect('main:playlist_{}_book'.format(self.mode), **self.kwargs)
        book_session_list = self.request.session.get(SESSION_KEY_BOOK)

        # create Books if not exists
        book_dict_list = [
            {
                'isbn': book_session['isbn'],
                'created_at': timezone.now(),
                'updated_at': timezone.now(),
            }
            for book_session in book_session_list
        ]
        book_obj_list = [Book(**book_dict) for book_dict in book_dict_list]
        Book.objects.bulk_create(book_obj_list, ignore_conflicts=True)

        # create BookData if not exists
        book_data_dict_list = [
            {
                'book_id': book_session['isbn'],
                'provider_id': book_session['provider_id'],
                'title': book_session['title'],
                'author': book_session['author'],
                'publisher': book_session['publisher'],
                'cover': book_session['cover'],
                'created_at': timezone.now(),
                'updated_at': timezone.now(),
            }
            for book_session in book_session_list
        ]
        book_data_obj_list = [BookData(**book_data_dict) for book_data_dict in book_data_dict_list]
        BookData.objects.bulk_create(book_data_obj_list, ignore_conflicts=True)

        # save Playlists and PlaylistBooks
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
        if self.success_message:
            messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def form_invalid(self, form):
        formset = PlaylistBookFormSet(self.request.POST, instance=self.object, form_kwargs={'request': self.request})
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


@login_required
class PlaylistCreateView(BasePlaylistFormView):
    mode = MODE_CREATE
    success_message = None
    template_name = 'main/playlist/create.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        self.initial_form_data =  None
        self.initial_book_data = []
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        self.success_url = reverse_lazy('main:playlist_create_complete', kwargs={'pk': str(self.object.pk)})
        return super().get_success_url()


@login_required
class PlaylistUpdateView(OwnerOnlyMixin, BasePlaylistFormView):
    mode = MODE_UPDATE
    success_message = _('Playlist updated successfully.')
    template_name = 'main/playlist/update.html'

    def get(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        self.initial_form_data =  None
        self.initial_book_data = [
            {
                'isbn': x.book.isbn,
                'provider_id': str(x.book.data.provider.pk),
                'title': x.book.data.title,
                'author': x.book.data.author,
                'publisher': x.book.data.publisher,
                'cover': x.book.data.cover,
            }
            for x in self.object.playlist_book_set.all()
        ]
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        self.success_url = reverse_lazy('main:playlist_detail', kwargs=self.kwargs)
        return super().get_success_url()


@login_required
class BasePlaylistBookView(SearchFormView):
    form_class = BookSearchForm
    template_name = 'main/playlist/book.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mode'] = self.mode
        kwargs['pk'] = self.kwargs.get('pk')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = self.mode
        return context


class PlaylistCreateBookView(BasePlaylistBookView):
    mode = MODE_CREATE


class PlaylistUpdateBookView(OwnerOnlyMixin, BasePlaylistBookView):
    mode = MODE_UPDATE


@csrf_protect
@login_required
class BookSearchView(APIMixin, generic.View):

    def search_book(self, data):
        q = data.get('q')
        if not self.request.is_ajax() or not q:
            return HttpResponseBadRequest()

        if self.provider.slug == 'rakuten':
            params = {
                'applicationId': settings.RAKUTEN_APPLICATION_ID,
                'hits': '24',
                'title': q,
                'sort': 'reviewCount',
            }
            page = data.get('page')
            if page:
                params['page'] = page
        else:
            params = {}

        response = self.get_book_data(params)
        if response.status_code == requests.codes.bad_request:
            return HttpResponse(_('<p class="mt-4">The keyword is too short. Please search by longer words.</p>'))
        elif 'error' in response:
            return HttpResponse(_('<p class="mt-4">An error has occurred. Please retry later.</p>'))

        response = response.json()
        context = {
            'mode': data.get('mode'),
            'pk': data.get('pk'),
            'books_in_session': [x['isbn'] for x in self.request.session.get(SESSION_KEY_BOOK)] if SESSION_KEY_BOOK in self.request.session else [],
            'count': response['count'],
            'first': response['first'],
            'last': response['last'],
            'books': [
                {
                    'isbn': self.format_isbn(book['Item']['isbn']),
                    'title': self.format_title(book['Item']['title'], book['Item']['subTitle'], book['Item']['contents']),
                    'author': book['Item']['author'],
                    'cover': book['Item']['largeImageUrl'],
                }
                for book in response['Items']
            ]
        }

        url_params = {k: data[k] for k in data.keys() if k not in ('csrfmiddlewaretoken', 'page',)}
        if int(response['count']):
            context['page_obj'] = Paginator(range(int(response['count'])), 24).page(int(response['page']))
            context['params'] = url_params
        return render(
            self.request,
            'main/playlist/layouts/book-list.html',
            context
        )

    def get(self, request, *args, **kwargs):
        return self.search_book(request.GET.copy())

    def post(self, request, *args, **kwargs):
        return self.search_book(request.POST.copy())


@login_required
class BasePlaylistBookStoreView(APIMixin, generic.RedirectView):

    def get(self, request, *args, **kwargs):
        form_data = request.session.get(SESSION_KEY_FORM)
        book_data = request.session.get(SESSION_KEY_BOOK)
        if not form_data or not SESSION_KEY_BOOK in request.session:
            messages.warning(request, _('Session timeout. Please retry from the beginning.'))
            return redirect('main:playlist_{}'.format(self.mode), **self.kwargs)

        book_obj = Book.objects.filter(isbn=self.kwargs.get('isbn')).first()
        if book_obj and book_obj.data:
            book_json = {
                'isbn': self.kwargs.get('isbn'),
                'provider_id': str(book_obj.data.provider.pk),
                'title': book_obj.data.title,
                'author': book_obj.data.author,
                'publisher': book_obj.data.publisher,
                'cover': book_obj.data.cover,
            }
        else:
            if self.provider.slug == 'rakuten':
                params = {
                    'applicationId': settings.RAKUTEN_APPLICATION_ID,
                    'isbn': self.kwargs.get('isbn'),
                }
            else:
                params = {}
            response = self.get_book_data(params)
            if 'error' in response:
                return HttpResponseServerError()
            response = response.json()
            if int(response['count']) == 0:
                return HttpResponseServerError()
            book = response['Items'][0]
            book_json = {
                'isbn': self.kwargs.get('isbn'),
                'provider_id': str(self.provider.pk),
                'title': self.format_title(book['Item']['title'], book['Item']['subTitle'], book['Item']['contents']),
                'author': book['Item']['author'],
                'publisher': book['Item']['publisherName'],
                'cover': book['Item']['largeImageUrl'],
            }
        if book_json not in request.session.get(SESSION_KEY_BOOK):
            request.session[SESSION_KEY_BOOK] += [book_json]
            book_num = len(request.session[SESSION_KEY_BOOK])
            request.session[SESSION_KEY_FORM]['playlist_book_set-{}-book'.format(book_num-1)] = book_json['isbn']
            request.session[SESSION_KEY_FORM]['playlist_book_set-TOTAL_FORMS'] = str(int(request.session[SESSION_KEY_FORM]['playlist_book_set-TOTAL_FORMS']) + 1)
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        del self.kwargs['isbn']
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


class CreateOrSignupView(generic.RedirectView):
    url = reverse_lazy('main:playlist_create')

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:signup')
        return super().get(request, *args, **kwargs)


class TermsView(generic.TemplateView):
    template_name = 'main/terms.html'


class PrivacyView(generic.TemplateView):
    template_name = 'main/privacy.html'


class AboutView(generic.TemplateView):
    template_name = 'main/about.html'


class ContactView(generic.FormView):
    form_class = ContactForm
    success_url = reverse_lazy('main:contact_complete')
    template_name = 'main/contact.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'request': self.request,
        }
        form.save(**opts)
        return super().form_valid(form)


class ContactCompleteView(generic.TemplateView):
    template_name = 'main/contact_complete.html'
