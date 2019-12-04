import re

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

    fields = dict((name, kwargs.get(name, details.get(name))) for name in USER_FIELDS)
    if not fields:
        return
    elif not fields['email']:
        messages.error(request, _('We cannot get your email address. Please modify the settings on your SNS account.'))
        return redirect('accounts:signup')
    elif not fields['username']:
        fields['username'] = [x for x in re.split('[^0-9a-zA-Z_]+', fields['email']) if x][0]

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }
