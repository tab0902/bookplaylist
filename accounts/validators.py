from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class UnicodeUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.]+\Z'
    message = _(
        '有効なユーザー名を入力してください。半角英数、ピリオド、アンダーバーを使用できます。'
    )
    flags = 0
