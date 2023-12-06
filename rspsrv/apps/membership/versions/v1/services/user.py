from datetime import datetime

import jwt
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import exceptions
from rest_framework_jwt.utils import jwt_decode_handler

from rspsrv.apps.membership.models import User, UserRecoverPasswordToken
from rspsrv.apps.membership.versions.v1.serializers.user import (
    CreateUserSerializer,
    UserSetPasswordSerializer,
    UserLoginSerializer,
    UserGenerateTokenSerializer,
    UserSerializer,
    UserEmpowerSerializer,
    UserRenewPasswordSerializer,
    UserRecoverPasswordSerializer,
)
from rspsrv.apps.membership.versions.v1.services.common import RecoverEmail
from rspsrv.apps.membership.versions.v1.services.mfa import MFAService
from rspsrv.apps.mis.versions.v1_0.services.mis import MisService
from rspsrv.tools import api_exceptions
from rspsrv.tools.utility import Helper


class UserService:
    @classmethod
    def create_user(cls, params, context=True):
        """
        Creating a new user using UserSerializer
        :param context: True for email and mobile to be required
        :param params:
        :return:
        """
        user_serializer = CreateUserSerializer(data=params, context=context)
        if not user_serializer.is_valid():
            raise api_exceptions.ValidationError400(user_serializer.errors)

        user_data = user_serializer.data
        raw_password = user_data.pop("password")
        group = user_data.pop("group")

        if Helper.is_password_weak(raw_password):
            raise api_exceptions.ValidationError400(
                {
                    "password": _("Password is weak")
                }
            )

        user = User(**user_data)
        user.set_password(raw_password)
        user.save()
        user.groups.add(group)

        data = user_serializer.data
        data['id'] = user.id
        data['prime_code'] = \
            user.customer.prime_code if user.customer else None
        if 'customer_id' in data:
            data.pop('customer_id')

        return data

    @classmethod
    def force_set_password(
            cls,
            body,
            groups,
            user_id
    ):
        """
        Force set password without any token
        :param body:
        :param groups:
        :param user_id:
        :return:
        """
        set_password = UserSetPasswordSerializer(
            data=body,
        )
        if set_password.is_valid(raise_exception=True):
            try:
                user = User.objects.get(
                    id=user_id,
                    groups__name__in=groups
                )
            except User.DoesNotExist:
                raise api_exceptions.NotFound404(
                    _("Can not find user with this privilege level")
                )

            user.set_password(set_password.data['new_password1'])
            user.save()

            return True

    @classmethod
    def login_user(cls, body):
        """
        Check if login data is valid
        :param body:
        :return:
        """
        login_serializer = UserLoginSerializer(
            data=body,
        )
        if not login_serializer.is_valid():
            raise api_exceptions.ValidationError400(login_serializer.errors)

        return login_serializer.data

    @classmethod
    def delete_user(cls, groups, user_id):
        """
        Soft delete a user
        :param groups:
        :param user_id:
        :return:
        """
        try:
            user = User.objects.get(
                id=user_id,
                groups__name__in=groups
            )
        except User.DoesNotExist:
            raise api_exceptions.NotFound404(
                _("Can not find user with this privilege level")
            )

        user.deleted = True
        user.save()

        return True

    @classmethod
    def update_user(cls, groups, body, user_id):
        """
        Update users' data based on access groups
        :param groups:
        :param body:
        :param user_id:
        :return:
        """
        try:
            user = User.objects.get(
                id=user_id,
            )
        except User.DoesNotExist:
            raise api_exceptions.NotFound404(
                _("Can not find user with this identifier")
            )
        if any(g not in groups for g in user.groups.all().values_list(
                'name',
                flat=True,
        )):
            raise api_exceptions.PermissionDenied403(
                _("Can not update this user with your privilege level")
            )
        user_serializer = UserSerializer(
            user,
            data=body,
            partial=True,
        )

        if not user_serializer.is_valid():
            raise api_exceptions.ValidationError400(user_serializer.errors)

        user_serializer.save()

        return user_serializer.data

    @classmethod
    def empower_user(cls, body, groups, user_id):
        """
        Activate or deactivate a user
        :param body:
        :param groups:
        :param user_id:
        :return:
        """
        user_serializer = UserEmpowerSerializer(
            data=body,
        )

        if not user_serializer.is_valid():
            raise api_exceptions.ValidationError400(user_serializer.errors)
        try:
            user = User.objects.get(
                id=user_id,
                groups__name__in=groups
            )
        except User.DoesNotExist:
            raise api_exceptions.NotFound404(
                _("Can not find user with this privilege level")
            )
        if not user.is_active and user_serializer.data["is_active"]:
            # Check for duplicates
            if User.objects.filter(
                    Q(username=user.username) |
                    Q(email=user.email) |
                    Q(mobile=user.mobile),
                    customer=user.customer,
                    is_active=True,
                    deleted=False,
            ).exists():
                raise api_exceptions.Conflict409(_(
                    "Another active user with theses credentials is already "
                    "exists"
                ))
        user.is_active = user_serializer.data["is_active"]
        user.save()

        return True

    @classmethod
    def renew_password(cls, user_id, body):
        """
        Force set password for a user
        :param user_id:
        :param body:
        :return:
        """
        try:
            user_object = User.objects.get(
                id=user_id,
            )
        except User.DoesNotExist:
            raise api_exceptions.NotFound404({
                "username": _("User does not exists")
            })
        reset_serializer = UserRenewPasswordSerializer(
            data=body,
        )
        if not reset_serializer.is_valid():
            raise api_exceptions.ValidationError400(reset_serializer.errors)

        old_pass = reset_serializer.data['old_password']
        new_pass = reset_serializer.data['new_password1']
        if not user_object.check_password(old_pass):
            raise api_exceptions.ValidationError400(
                {
                    "old_password": _("Old password is incorrect")
                }
            )
        user_object.set_password(new_pass)
        user_object.save()

        return True

    @classmethod
    def recover_password(cls, prime_code, key):
        """
        Create and send recover token for a user (MIS included)
        :param prime_code:
        :param key:
        :return:
        """
        try:
            user = User.objects.get(
                Q(username=key) | Q(email__iexact=key),
                customer__id=prime_code,
                is_active=True,
                deleted=False,
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            raise api_exceptions.NotFound404(
                _("User does not exists")
            )

        payload = {
            'id': user.id,
            'exp': datetime.utcnow() +
                   settings.USER_RECOVER_PASSWORD_TOKEN_EXPIRE
        }

        token = Helper.jwt_encode(payload=payload)
        recover_token = UserRecoverPasswordToken(token=token)
        recover_token.save()

        RecoverEmail.send_recover_email(
            user,
            token,
        )

        return True

    @classmethod
    def recover_password_confirm(cls, token):
        """
        Check if recover password token is valid (expiry, connected user and
        usages)
        :param token:
        :return:
        """
        try:
            payload = jwt_decode_handler(token)
        except (jwt.ExpiredSignature, jwt.DecodeError):
            raise api_exceptions.PermissionDenied403(
                {
                    'token': _("Token is expired")
                }
            )
        try:
            user_recover_token = UserRecoverPasswordToken.objects.get(
                token=token,
            )
        except (
                UserRecoverPasswordToken.DoesNotExist,
                UserRecoverPasswordToken.MultipleObjectsReturned,
        ):
            raise api_exceptions.NotFound404(
                {
                    'token': _("Token does not exists")
                }
            )
        if user_recover_token.is_used:
            raise api_exceptions.Conflict409(
                {
                    'token': _("This token is already used")
                }
            )
        id = payload.get('id')
        try:
            user = User.objects.get(id=id)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            raise api_exceptions.NotFound404(
                {
                    'id': _("User does not exists")
                }
            )

        return user, user_recover_token

    @classmethod
    def recover_password_reset(cls, body):
        """
        Force reset password if recover token exists
        :param body:
        :return:
        """
        recover = UserRecoverPasswordSerializer(data=body)
        if not recover.is_valid():
            raise api_exceptions.ValidationError400(recover.errors)

        confirm_data = cls.recover_password_confirm(recover.data['token'])
        user = confirm_data[0]
        user_recover_token = confirm_data[1]
        user_recover_token.is_used = True
        user_recover_token.save()
        user.set_password(recover.data['new_password1'])
        user.save()

        return True

    @classmethod
    def generate_token(cls, body):
        """
        Generate a token using MFAConfig service
        :param body:
        """
        generate = UserGenerateTokenSerializer(data=body)
        if not generate.is_valid():
            raise api_exceptions.ValidationError400(generate.errors)
        mobile = cls.get_mobile(
            generate.data['prime_code'],
            generate.data['username'],
        )
        if mobile is None:
            raise api_exceptions.NotFound404(
                _("Mobile number does not exists for these credentials")
            )
        if not Helper.is_mobile_number(mobile):
            raise api_exceptions.ValidationError400(
                _("Mobile number is not valid")
            )
        try:
            MFAService.generate(mobile=mobile)
        except exceptions.APIException:
            raise

        return f"{mobile[:2]}******{mobile[-3:]}"

    @classmethod
    def get_mobile(cls, prime_code, username):
        """
        Get the mobile number of user based on prime_code a username
        :param prime_code:
        :param username:
        """
        if prime_code is None:
            try:
                user = User.objects.get(
                    is_active=True,
                    deleted=False,
                    username=username,
                    customer__isnull=True,
                )
                return user.mobile
            except User.DoesNotExist:
                return None
        else:
            try:
                user = User.objects.get(
                    is_active=True,
                    customer__id=prime_code,
                    username=username,
                    deleted=False,
                )
            except User.DoesNotExist:
                return None
            if username != settings.CRM_APP.DEFAULT_CUSTOMER_ADMIN_USERNAME:
                return user.mobile
            else:
                subscriptions = user.customer.subscriptions.filter(
                    is_allocated=True,
                )[:1]
                if subscriptions:
                    subscription_code = subscriptions[0].subscription_code
                    return MisService.get_mobile(
                        subscription_code=subscription_code,
                    )

        return None
