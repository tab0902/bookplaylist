from django.urls import path, re_path

from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('playlists/', views.PlaylistView.as_view(), name='playlist'),
    path('playlists/create/', views.PlaylistCreateView.as_view(), name='playlist_create'),
    path('playlists/create/book/', views.PlaylistCreateBookView.as_view(), name='playlist_create_book'),
    re_path(r'playlists/create/book/(?P<isbn>\d{13})/', views.PlaylistCreateBookStoreView.as_view(), name='playlist_create_book_store'),
    path('playlists/create/complete/<uuid:pk>/', views.PlaylistCreateCompleteView.as_view(), name='playlist_create_complete'),
    path('playlists/<uuid:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlists/<uuid:pk>/update/', views.PlaylistUpdateView.as_view(), name='playlist_update'),
    path('playlists/<uuid:pk>/update/book/', views.PlaylistUpdateBookView.as_view(), name='playlist_update_book'),
    re_path(
        r'playlists/(?P<pk>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/update/book/(?P<isbn>\d{13})/',
        views.PlaylistUpdateBookStoreView.as_view(),
        name='playlist_update_book_store'
    ),
    path('playlists/<uuid:pk>/delete/', views.PlaylistDeleteView.as_view(), name='playlist_delete'),
    path('playlists/create-or-signup/', views.CreateOrSignupView.as_view(), name='create_or_signup'),
    path('book/search/', views.BookSearchView.as_view(), name='book_search'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/complete/', views.ContactCompleteView.as_view(), name='contact_complete'),
]
