from django.contrib import auth
from django.contrib.auth.base_user import (
    AbstractBaseUser, BaseUserManager,
)
from django.contrib.auth.models import PermissionsMixin
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import UnicodeUsernameValidator
from bookplaylist.models import (
    BaseModel, NullCharField, NullEmailField, NullTextField,
)


# Create your models here.


class UserManager(BaseUserManager):
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


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = NullCharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and _ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = NullEmailField(
        _('email address'),
        unique=True,
        blank=True,
        null=True,
        help_text=_('Required. Enter a valid email address.'),
        error_messages={
            'unique': _("A user with that email address already exists."),
        },
    )
    first_name = NullCharField(_('first name'), max_length=30, blank=True, null=True)
    last_name = NullCharField(_('last name'), max_length=150, blank=True, null=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    date_verified = models.DateTimeField(_('date verified'), blank=True, null=True)
    comment = NullTextField(_('comment'), blank=True, null=True)
    twitter_id = NullCharField(_('Twitter ID'), max_length=255, unique=True, blank=True, null=True)
    facebook_id = NullCharField(_('Facebook ID'), max_length=255, unique=True, blank=True, null=True)
    hopes_newsletter = models.BooleanField(_('newsletter status'), default=True)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(BaseModel.Meta):
        db_table = 'users'
        ordering = ['-last_login']
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes =  [
            models.Index(fields=['date_joined'], name='date_joined'),
            models.Index(fields=['last_login'], name='last_login'),
        ] + BaseModel._meta.indexes

    def __str__(self):
        return '%s' % (self.get_username() or self.pk)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        full_name = '%s %s' % (self.last_name, self.first_name)
        return full_name.strip()

    def get_short_name(self):
        return self.username or self.uuid

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)
