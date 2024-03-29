import requests
from distutils.util import strtobool
from itertools import chain

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import (
    Count, Exists, OuterRef, Prefetch, Q,
)
from django.http import (
    Http404, HttpResponse, HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404, redirect, render,
)
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .forms import (
    BookSearchForm, ContactForm, PlaylistBookFormSet, PlaylistForm, PlaylistSearchForm,
)
from .models import (
    Book, BookData, Like, Playlist, Theme,
)
from bookplaylist.utils import APIMixin
from bookplaylist.views import (
    OwnerOnlyMixin, SearchFormView, TemplateContextMixin, csrf_protect, login_required,
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
        if theme:
            self.param['theme'] = theme.slug
        return super().form_valid(form)


class IndexView(TemplateContextMixin, PlaylistSearchFormView):
    og_type = 'website'
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'playlists_recommended': Playlist.objects \
                .filter(sequence__isnull=False) \
                .order_by('sequence'),
            'playlists_popular': Playlist.objects \
                .filter(
                    playlist_book__deleted_at__isnull=True,
                    like__deleted_at__isnull=True) \
                .annotate(
                    playlist_book__count=Count('playlist_book', distinct=True),
                    like__count=Count('like', distinct=True)) \
                .filter(
                    playlist_book__count__gte=2) \
                .order_by(
                    '-like__count',
                    '-created_at') \
                 [:4],
            'playlists_recent': Playlist.objects \
                .filter(
                    playlist_book__deleted_at__isnull=True) \
                .annotate(
                    playlist_book__count=Count('playlist_book',distinct=True)) \
                .filter(
                    playlist_book__count__gte=2) \
                .order_by(
                    '-created_at') \
                 [:4],
            'themes': Theme.objects \
                .prefetch_related(
                    Prefetch(
                        'playlist_set',
                        queryset=Playlist.objects \
                            .filter(
                                recommendation__isnull=False,
                                recommendation__sequence__isnull=False) \
                            .order_by('recommendation__sequence')))
        })
        return context


class PlaylistView(TemplateContextMixin, generic.list.BaseListView, PlaylistSearchFormView):
    context_object_name = 'playlists'
    model = Playlist
    template_name = 'main/playlists/list.html'

    def get_queryset(self):
        condition_list = []
        condition_dict = {}
        theme = self.request.GET.get('theme')
        query = self.request.GET.get('q')
        ordering = self.request.GET.get('ordering') or 'popular'

        if theme:
            condition_dict['theme__slug'] = theme
        if query:
            q_list = self._format_query(query)
            condition_list = [
                  Q(title__icontains=q)\
                | Q(description__icontains=q)\
                | Q(playlist_book__book__book_data__title__icontains=q)\
                | Q(playlist_book__book__book_data__author__icontains=q)
                | Q(playlist_book__book__book_data__publisher__icontains=q)
                for q in q_list
            ]

        queryset = Playlist.objects.filter(*condition_list, **condition_dict).distinct()

        if ordering == 'popular':
            queryset = queryset \
                .filter(like__deleted_at__isnull=True) \
                .annotate(like__count=Count('like',distinct=True)) \
                .order_by('-like__count', '-created_at')
        elif ordering == 'recent':
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        q = self.request.GET.get('q')
        ordering = self.request.GET.get('ordering')
        theme_slug = self.request.GET.get('theme')
        theme = Theme.objects.filter(slug=theme_slug).first()

        # page_title
        if q:
            self.page_title = _('Playlists related with "%(q)s"') % {'q': q}
        elif theme_slug and theme:
            self.page_title = _('Playlists with %(theme)s') % {'theme': theme.tagged_name}
        elif ordering == 'popular':
            self.page_title = _('All popular playlists')
        elif ordering == 'recent':
            self.page_title = _('All recent playlists')
        else:
            self.page_title = _('All playlists')

        # page_description
        if theme:
            self.page_description = theme.description
        else:
            self.page_description = ''

        self.og_url =  self.request.build_absolute_uri()
        context = super().get_context_data(**kwargs)
        context['theme'] = theme
        return context


class PlaylistDetailView(TemplateContextMixin, generic.DetailView):
    model = Playlist
    template_name = 'main/playlists/detail.html'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('theme')
        if self.request.user.is_authenticated:
            like = Like.objects.filter(
                playlist=OuterRef('pk'),
                user=self.request.user,
            )
            queryset = queryset.annotate(is_liked=Exists(like))
        return queryset

    def get_context_data(self, **kwargs):
        self.page_title = self.object.title
        self.page_description = \
            self.object.description or \
            'BooxMixのプレイリスト詳細画面では、おすすめの本が詰まったプレイリストを閲覧することができます。入門書から個性のある本まで、多様な順番でまとめられています。興味ある本を発見したら購入してみましょう。'
        self.og_url =  self.request.build_absolute_uri()
        self.og_image =  self.object.og_image.url
        self.og_image_width = settings.OG_IMAGE_WIDTH
        self.og_image_height = settings.OG_IMAGE_HEIGHT

        context = super().get_context_data(**kwargs)
        context['other_playlists'] = Playlist.objects \
            .exclude(
                pk=self.object.pk) \
            .filter(
                theme=self.object.theme,
                playlist_book__deleted_at__isnull=True,
                like__deleted_at__isnull=True) \
            .annotate(
                playlist_book__count=Count('playlist_book', distinct=True),
                like__count=Count('like', distinct=True)) \
            .filter(
                playlist_book__count__gte=2) \
            .order_by(
                '-like__count',
                '-created_at') \
             [:4]
        return context


MODE_CREATE = 'create'
MODE_UPDATE = 'update'
GET_KEY_CONTINUE = 'continue'
POST_KEY_SEARCH = 'search'
POST_KEY_ADD_BOOK = 'add_book'
SESSION_KEY_FORM = 'playlist_form_data'
SESSION_KEY_BOOK = 'playlist_book_data'


class BasePlaylistFormView(APIMixin, generic.detail.SingleObjectTemplateResponseMixin, generic.edit.ModelFormMixin, generic.edit.ProcessFormView):
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
        context.update({
            'formset': formset,
            'book_formset': zip(formset or [], book_data or []),
        })
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
            self._get_book_data_if_not_exists(book_session)
            for book_session in book_session_list
        ]
        book_data_obj_list = [BookData(**book_data_dict) for book_data_dict in book_data_dict_list]
        BookData.objects.bulk_create(book_data_obj_list, ignore_conflicts=True)

        # handle PlaylistBookFormSet
        instance = form.save(commit=False)
        formset = PlaylistBookFormSet(self.request.POST, instance=instance, form_kwargs={'request': self.request})
        if not len(formset.forms) - len(formset.deleted_forms):
            messages.error(self.request, _('You have to add at least one book to your playlist.'))
            self.request.session[SESSION_KEY_FORM] = self.request.POST
            url = self.get_error_url()
            return HttpResponseRedirect(url)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        # save Playlist and PlaylistBooks
        instance.save()
        formset.save()

        # save Playlist.og_image
        instance.save_og_image()

        # clear session and redirect
        for key in (SESSION_KEY_FORM, SESSION_KEY_BOOK,):
            if SESSION_KEY_FORM in self.request.session:
                del self.request.session[key]
        if self.success_message:
            messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def form_invalid(self, form):
        formset = PlaylistBookFormSet(self.request.POST, instance=self.object, form_kwargs={'request': self.request})
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def get_error_url(self):
        return reverse_lazy('main:playlist_{}'.format(self.mode), kwargs=self.kwargs) + '?{}=True'.format(GET_KEY_CONTINUE)

    def _get_book_data_if_not_exists(self, book_session):
        if book_session['provider_id'] == str(self.provider.pk):
            # if the same data is in db, return existing BookData
            return self._book_session_to_book_data_dict(book_session)

        if self.provider.slug == 'rakuten':
            params = {
                'applicationId': settings.RAKUTEN_APPLICATION_ID,
                'isbn': book_session['isbn'],
            }
        else:
            params = {}
        response = self.get_book_data(params).json()
        if not response or not response[0] == 'null' or 'error' in response or int(response['count']) == 0:
            # if no data is in the response, return existing BookData
            return self._book_session_to_book_data_dict(book_session)
        book = response['Items'][0]
        book_data_dict = {
            'book_id': book_session['isbn'],
            'provider_id': str(self.provider.pk),
            'title': self.format_title(book['Item']['title'], book['Item']['subTitle'], book['Item']['contents']),
            'author': book['Item']['author'],
            'publisher': book['Item']['publisherName'],
            'cover': book['Item']['largeImageUrl'],
            'created_at': timezone.now(),
            'updated_at': timezone.now(),
        }
        return book_data_dict

    def _book_session_to_book_data_dict(self, book_session):
        book_data_dict = {
            'book_id': book_session['isbn'],
            'provider_id': book_session['provider_id'],
            'title': book_session['title'],
            'author': book_session['author'],
            'publisher': book_session['publisher'],
            'cover': book_session['cover'],
            'created_at': timezone.now(),
            'updated_at': timezone.now(),
        }
        return book_data_dict


@login_required
class PlaylistCreateView(TemplateContextMixin, BasePlaylistFormView):
    mode = MODE_CREATE
    page_title = _('Create book playlist')
    page_description = \
        'BooxMixのプレイリスト作成画面では、あなたがおすすめしたい本を追加して、本のプレイリストを作成することができます。本の追加もコメントも簡単でシンプルにできます。完成したらTwitterで友達に共有しましょう。'
    success_message = None
    template_name = 'main/playlists/create.html'

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
class PlaylistUpdateView(TemplateContextMixin, OwnerOnlyMixin, BasePlaylistFormView):
    mode = MODE_UPDATE
    page_title = _('Update playlist')
    success_message = _('Playlist updated successfully.')
    template_name = 'main/playlists/update.html'

    def get(self, request, *args, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        self.initial_form_data =  None
        self.initial_book_data = [
            {
                'isbn': x.book.isbn,
                'provider_id': str(x.book._default_data.provider.pk),
                'title': x.book._default_data.title,
                'author': x.book._default_data.author,
                'publisher': x.book._default_data.publisher,
                'cover': x.book._default_data.cover,
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

    def get_context_data(self, **kwargs):
        self.og_url = self.get_full_absolute_url(self.object)
        self.og_image = self.object.og_image.url
        self.og_image_width = settings.OG_IMAGE_WIDTH
        self.og_image_height = settings.OG_IMAGE_HEIGHT
        return super().get_context_data(**kwargs)


@login_required
class BasePlaylistBookView(TemplateContextMixin, SearchFormView):
    form_class = BookSearchForm
    page_title = _('Search book to add')
    template_name = 'main/playlists/book.html'

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
            raise Http404

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

        response = response.json()
        if 'error' in response:
            return HttpResponse(_('<p class="mt-4">An error has occurred. Please retry later.</p>'))

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
            'main/playlists/layouts/book-list.html',
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
        if book_obj and book_obj._default_data:
            book_json = {
                'isbn': self.kwargs.get('isbn'),
                'provider_id': str(book_obj._default_data.provider.pk),
                'title': book_obj._default_data.title,
                'author': book_obj._default_data.author,
                'publisher': book_obj._default_data.publisher,
                'cover': book_obj._default_data.cover,
            }
        else:
            if self.provider.slug == 'rakuten':
                params = {
                    'applicationId': settings.RAKUTEN_APPLICATION_ID,
                    'isbn': self.kwargs.get('isbn'),
                }
            else:
                params = {}
            response = self.get_book_data(params).json()
            if 'error' in response:
                messages.error(_('An error has occurred. Please retry later.'))
                url = self.get_redirect_url()
                return HttpResponseRedirect(url)
            if int(response['count']) == 0:
                messages.error(_('We could\'t find the book you want to add. Please retry again.'))
                url = self.get_redirect_url()
                return HttpResponseRedirect(url)
            book = response['Items'][0]
            book_json = {
                'isbn': self.kwargs.get('isbn'),
                'provider_id': str(self.provider.pk),
                'title': self.format_title(book['Item']['title'], book['Item']['subTitle'], book['Item']['contents']),
                'author': book['Item']['author'],
                'publisher': book['Item']['publisherName'],
                'cover': book['Item']['largeImageUrl'],
            }

        if book_json in request.session.get(SESSION_KEY_BOOK):
            messages.error(request, _('This book has already been added to the playlist.'))
            url = self.get_redirect_url()
            return HttpResponseRedirect(url)

        request.session[SESSION_KEY_BOOK] += [book_json]
        book_num = len(request.session[SESSION_KEY_BOOK])
        request.session[SESSION_KEY_FORM]['playlist_book_set-{}-book'.format(book_num-1)] = book_json['isbn']
        request.session[SESSION_KEY_FORM]['playlist_book_set-TOTAL_FORMS'] = str(int(request.session[SESSION_KEY_FORM]['playlist_book_set-TOTAL_FORMS']) + 1)
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        isbn = self.kwargs['isbn']
        del self.kwargs['isbn']
        self.url = reverse_lazy('main:playlist_{}'.format(self.mode), kwargs=self.kwargs) + '?{param}=True#{isbn}'.format(param=GET_KEY_CONTINUE, isbn=isbn)
        return super().get_redirect_url(*args, **kwargs)


class PlaylistCreateBookStoreView(BasePlaylistBookStoreView):
    mode = MODE_CREATE


class PlaylistUpdateBookStoreView(OwnerOnlyMixin, BasePlaylistBookStoreView):
    mode = MODE_UPDATE


@login_required
class PlaylistCreateCompleteView(TemplateContextMixin, OwnerOnlyMixin, generic.DetailView):
    model = Playlist
    page_title = _('Playlist created successfully!')
    page_description = \
        'BooxMixのプレイリスト完成画面では、作成したプレイリストを気軽にTwitterでシェアすることができます。あなたの知識や経験を本を通して友達に共有しましょう。BooxMixは、気軽に本を複数冊まとめてプレイリストを作成し、SNSでシェアできるウェブサービスです。'
    template_name = 'main/playlists/create_complete.html'

    def get_context_data(self, **kwargs):
        self.og_url = self.get_full_absolute_url(self.object)
        self.og_image = self.object.og_image.url
        self.og_image_width = settings.OG_IMAGE_WIDTH
        self.og_image_height = settings.OG_IMAGE_HEIGHT
        return super().get_context_data(**kwargs)


@login_required
class PlaylistDeleteView(TemplateContextMixin, OwnerOnlyMixin, generic.DeleteView):
    model = Playlist
    page_title = _('Delete playlist')
    success_url = reverse_lazy('accounts:index')
    template_name = 'main/playlists/delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Playlist deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@csrf_protect
class PlaylistLikeView(generic.View):

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        playlist = get_object_or_404(Playlist, pk=self.kwargs.get('pk'))
        user = request.user
        likes_count = int(request.POST.get('count'))
        is_liked_req = strtobool(request.POST.get('is_liked'))
        if not user.is_authenticated:
            is_guest_user = True
            is_liked = is_liked_req
        else:
            is_guest_user = False
            like = Like.all_objects.filter(playlist=playlist, user=user).first()
            is_liked = bool(like and not like.is_deleted)

            # If like-status in the request is correct, update data in DB.
            if is_liked == is_liked_req:
                if not like:
                    like = playlist.likes.create(user=user)
                elif like.is_deleted:
                    like.restore()
                elif not like.is_deleted:
                    like.delete()

            is_liked = bool(like and not like.is_deleted)
            likes_count = likes_count + 1 if not is_liked_req else likes_count - 1

        context = {
            'playlist_id': playlist.pk,
            'is_liked': is_liked,
            'likes_count': likes_count,
            'is_guest_user': is_guest_user,
        }
        return render(
            request,
            'main/playlists/layouts/like-button.html',
            context
        )


class CreateOrSignupView(generic.RedirectView):
    url = reverse_lazy('main:playlist_create')

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:signup')
        return super().get(request, *args, **kwargs)


class TermsView(TemplateContextMixin, generic.TemplateView):
    page_title = _('Terms')
    template_name = 'main/terms.html'


class PrivacyView(TemplateContextMixin, generic.TemplateView):
    page_title = _('Privacy policy')
    template_name = 'main/privacy.html'


class AboutView(TemplateContextMixin, generic.TemplateView):
    page_title = _('About BooxMix')
    template_name = 'main/about.html'


class ContactView(TemplateContextMixin, generic.FormView):
    form_class = ContactForm
    page_title = _('Contact')
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


class ContactCompleteView(TemplateContextMixin, generic.TemplateView):
    page_title = _('We recieve your inquiry')
    template_name = 'main/contact_complete.html'
