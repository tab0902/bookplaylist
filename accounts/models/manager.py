from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone

from bookplaylist.models import (
    AllObjectsManager, Manager,
)


__all__ = ['AllUserManager', 'UserManager', 'UserWithInactiveManager']


class CreateUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('date_verified', timezone.now())
        extra_fields.setdefault('hopes_newsletter', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)


class AllUserManager(CreateUserManager, AllObjectsManager):
    pass


class UserWithInactiveManager(CreateUserManager, Manager):
    pass


class UserManager(UserWithInactiveManager):

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
