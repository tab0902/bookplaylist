from django.urls import path, re_path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    re_path(r'users/(?P<username>[0-9a-zA-Z_]+)/', views.ProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup/complete/', views.SignupCompleteView.as_view(), name='signup_complete'),
    path('verification/<uidb64>/<token>/', views.VerificationView.as_view(), name='verification'),
    path('verification/again/', views.VerificationAgainView.as_view(), name='verification_again'),
    path('verification/sent/', views.VerificationSentView.as_view(), name='verification_sent'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('deactivate/', views.DeacrivateView.as_view(), name='deactivate'),
    path('deactivate/complete/', views.DeacrivateCompleteView.as_view(), name='deactivate_complete'),
]
