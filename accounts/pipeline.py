from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

USER_FIELDS = ['username', 'email']
UserModel = get_user_model()


def social_user(backend, uid, user=None, *args, **kwargs):
    provider = backend.name
    social = backend.strategy.storage.user.get_social_auth(provider, uid)
    if social:
        if user and social.user != user:
            messages.error(backend.strategy.request, _('This account is already in use.'))
            return redirect('accounts:settings')
        elif not user:
            user = social.user
    return {'social': social,
            'user': user,
            'is_new': user is None,
            'new_association': social is None}


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    # check if an inactive user with the same email address exists.
    user_inactive = UserModel.all_objects_without_deleted.filter(email=kwargs.get('email', details.get('email')), is_active=False).first()
    if user_inactive:
        messages.error(strategy.request, _('You can\'t register email address which is the same as a withdrawn user\'s one.'))
        return redirect('accounts:login')

    fields = dict((name, kwargs.get(name, details.get(name))) for name in USER_FIELDS)
    if not fields:
        return
    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }

def login_error(strategy, details, user=None, *args, **kwargs):
    if not user.is_active:
        messages.error(strategy.request, _('You can\'t register email address which is the same as a withdrawn user\'s one.'))
