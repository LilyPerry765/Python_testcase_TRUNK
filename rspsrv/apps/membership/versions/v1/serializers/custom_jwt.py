from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework_jwt.compat import PasswordField
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings

from rspsrv.apps.membership.versions.v1.services.mfa import MFAService
from rspsrv.apps.membership.versions.v1.services.user import UserService

User = get_user_model()
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class CustomJSONWebTokenSerializer(JSONWebTokenSerializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def __init__(self, *args, **kwargs):
        super(CustomJSONWebTokenSerializer, self).__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField(write_only=True)
        self.fields[self.prime_code_field] = serializers.CharField(
            default=None,
            allow_blank=True,
            allow_null=True,
        )
        self.fields[self.is_token_field] = serializers.BooleanField(
            default=False,
        )

    @property
    def prime_code_field(self):
        return "prime_code"

    @property
    def is_token_field(self):
        return "is_token"

    def validate(self, attrs):
        credentials = {
            self.prime_code_field: attrs.get(self.prime_code_field),
            self.is_token_field: attrs.get(self.is_token_field),
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }
        if credentials[self.username_field] and credentials['password']:
            if credentials[self.is_token_field]:
                try:
                    user = User.objects.get(
                        customer__id=credentials[self.prime_code_field],
                        username=credentials[self.username_field],
                        is_active=True,
                        deleted=False,
                    )
                except User.DoesNotExist:
                    user = None

                if user and not MFAService.validate(
                        mobile=UserService.get_mobile(
                            prime_code=credentials[self.prime_code_field],
                            username=credentials[self.username_field],
                        ),
                        token=credentials['password'],
                ):
                    msg = _('Unable to log in with provided credentials.')
                    raise serializers.ValidationError(msg)
            else:
                user = authenticate(**credentials)
            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                payload = jwt_payload_handler(user)

                return {
                    'token': jwt_encode_handler(payload),
                    'user': user
                }
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)
