from django import forms
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm

from .models import User


class UserCreationForm(BaseUserCreationForm):

    class Meta():
        model = User
        fields = ('username', 'email', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].required = True


class UserChangeForm(BaseUserChangeForm):

    class Meta:
        model = User
        fields = '__all__'
