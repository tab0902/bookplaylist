from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend as BaseModelBackend
from django.db.models import Q

UserModel = get_user_model()


class ModelBackend(BaseModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD) or kwargs.get(UserModel.EMANL_FIELD)
        if username is None or password is None:
            return
        try:
            user = UserModel.objects.get(Q(username=username)|Q(email=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
