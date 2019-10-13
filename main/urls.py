from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('playlist/', views.PlaylistView.as_view(), name='playlist'),
    path('playlist/<uuid:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlist/create/', views.PlaylistCreateView.as_view(), name='playlist_create'),
    path('playlist/create/complete/', views.PlaylistCreateCompleteView.as_view(), name='playlist_create_complete'),
]
