from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup/complete/', views.SignupCompleteView.as_view(), name='signup_complete'),
    path('verification/<uidb64>/<token>/', views.VerificationView.as_view(), name='verification'),
    path('verification/again/', views.VerificationAgainView.as_view(), name='verification_again'),
    path('verification/sent/', views.VerificationAgainSentView.as_view(), name='verification_sent'),
]
