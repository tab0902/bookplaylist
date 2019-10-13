from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('playlist/', views.PlaylistView.as_view(), name='playlist'),
    path('playlist/<uuid:pk>/', views.PlaylistDetailView.as_view(), name='playlist_detail'),
]