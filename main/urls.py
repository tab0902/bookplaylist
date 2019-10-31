from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('playlist/', views.PlaylistView.as_view(), name='playlist'),
    path('playlist/create/', views.PlaylistCreateView.as_view(), name='playlist_create'),
    path('playlist/create/book/', views.PlaylistCreateBookView.as_view(), name='playlist_create_book'),
    path('playlist/create/book/<uuid:book>/', views.PlaylistCreateBookStoreView.as_view(), name='playlist_create_book_store'),
    path('playlist/create/complete/<uuid:pk>/', views.PlaylistCreateCompleteView.as_view(), name='playlist_create_complete'),
    path('playlist/<slug:category>/<uuid:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlist/<slug:category>/<uuid:pk>/update/', views.PlaylistUpdateView.as_view(), name='playlist_update'),
    path('playlist/<slug:category>/<uuid:pk>/update/book/', views.PlaylistUpdateBookView.as_view(), name='playlist_update_book'),
    path('playlist/<slug:category>/<uuid:pk>/update/book/<uuid:book>/', views.PlaylistUpdateBookStoreView.as_view(), name='playlist_update_book_store'),
    path('playlist/<slug:category>/<uuid:pk>/delete/', views.PlaylistDeleteView.as_view(), name='playlist_delete'),
]
