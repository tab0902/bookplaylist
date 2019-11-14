from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('playlists/', views.PlaylistView.as_view(), name='playlist'),
    path('playlists/create/', views.PlaylistCreateView.as_view(), name='playlist_create'),
    path('playlists/create/book/', views.PlaylistCreateBookView.as_view(), name='playlist_create_book'),
    path('playlists/create/book/<uuid:book>/', views.PlaylistCreateBookStoreView.as_view(), name='playlist_create_book_store'),
    path('playlists/create/complete/<uuid:pk>/', views.PlaylistCreateCompleteView.as_view(), name='playlist_create_complete'),
    path('playlists/<uuid:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlists/<uuid:pk>/update/', views.PlaylistUpdateView.as_view(), name='playlist_update'),
    path('playlists/<uuid:pk>/update/book/', views.PlaylistUpdateBookView.as_view(), name='playlist_update_book'),
    path('playlists/<uuid:pk>/update/book/<uuid:book>/', views.PlaylistUpdateBookStoreView.as_view(), name='playlist_update_book_store'),
    path('playlists/<uuid:pk>/delete/', views.PlaylistDeleteView.as_view(), name='playlist_delete'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/complete/', views.ContactCompleteView.as_view(), name='contact_complete'),
]
