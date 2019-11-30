from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .manager import (
    AllUserManager, UserManager, UserWithInactiveManager,
)
from accounts.validators import UnicodeUsernameValidator
from bookplaylist.models import (
    BaseModel, NullCharField, NullEmailField, NullTextField,
)

# Create your models here.


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = NullCharField(
        _('username'),
        max_length=150,
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
    twitter_id = NullCharField(_('Twitter ID'), max_length=255, blank=True, null=True)
    facebook_id = NullCharField(_('Facebook ID'), max_length=255, blank=True, null=True)
    hopes_newsletter = models.BooleanField(_('newsletter status'), default=True)

    objects = UserManager()
    all_objects_without_deleted = UserWithInactiveManager()
    all_objects = AllUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta(BaseModel.Meta):
        db_table = 'users'
        ordering = ['-last_login']
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes =  [
            models.Index(fields=['username'], name='username'),
            models.Index(fields=['email'], name='email'),
            models.Index(fields=['date_joined'], name='date_joined'),
            models.Index(fields=['last_login'], name='last_login'),
        ] + BaseModel._meta.indexes
        constraints = [
            models.UniqueConstraint(fields=['username'], condition=models.Q(is_active=True, deleted_at__isnull=True), name='username'),
            models.UniqueConstraint(fields=['email'], condition=models.Q(is_active=True, deleted_at__isnull=True), name='email'),
            models.UniqueConstraint(fields=['twitter_id'], condition=models.Q(is_active=True, deleted_at__isnull=True), name='twitter_id'),
            models.UniqueConstraint(fields=['facebook_id'], condition=models.Q(is_active=True, deleted_at__isnull=True), name='facebook_id'),
        ]

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

    def get_absolute_url(self):
        return reverse_lazy('accounts:profile', args=[self.username])
