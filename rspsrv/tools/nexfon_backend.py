from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils.translation import gettext as _
from rest_framework import exceptions
from rest_framework_jwt.authentication import (
    JSONWebTokenAuthentication,
    jwt_get_username_from_payload,
)

UserModel = get_user_model()


class NexfonJSONWebTokenAuthentication(JSONWebTokenAuthentication):
    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        username = jwt_get_username_from_payload(payload)
        prime_code = payload["prime_code"] if "prime_code" in payload else None

        if not username:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = UserModel.objects.get(
                customer__id=prime_code,
                username=username,
                deleted=False,
                is_active=True,
            )
        except UserModel.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise exceptions.AuthenticationFailed(msg)

        return user


class NexfonModelBackend(ModelBackend):
    def authenticate(
            self,
            request,
            prime_code=None,
            username=None,
            password=None,
            **kwargs
    ):
        if prime_code is None:
            prime_code = kwargs.get('prime_code') if 'prime_code' in kwargs else None
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if password is None:
            password = kwargs.get('password')

        try:
            user = UserModel.objects.get(
                customer__id=prime_code,
                username=username,
                is_active=True,
                deleted=False,
            )
        except (ValueError, UserModel.DoesNotExist):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
