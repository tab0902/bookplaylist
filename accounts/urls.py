from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup/complete/', views.SignupCompleteView.as_view(), name='signup_complete'),
    path('signup/verification/<uidb64>/<token>/', views.VerificationView.as_view(), name='verification'),
]
