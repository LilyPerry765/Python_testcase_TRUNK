from django.contrib.auth.models import Group as GroupModel
from django.utils.translation import gettext as _
from rest_framework import serializers

from rspsrv.apps.membership.models import (
    User,
    Customer,
)
from rspsrv.apps.membership.versions.v1.configs import MembershipConfiguration
from rspsrv.tools.permissions import (
    Group,
)
from rspsrv.tools.utility import Helper


def get_group_name(groups):
    names = []
    for g in groups.all():
        names.append(g.name)

    return names


class UserSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        can_update = {}
        if "email" in validated_data:
            can_update['email'] = validated_data['email']
            if User.objects.filter(
                    email=validated_data['email'],
                    is_active=True,
                    deleted=False,
            ).exclude(
                guid=instance.guid,
            ).exists():
                raise serializers.ValidationError(
                    {
                        "email": _("This email is already exists")
                    }
                )
        if "mobile" in validated_data:
            if not Helper.is_mobile_number(
                    validated_data['mobile']
            ):
                raise serializers.ValidationError(
                    {
                        "mobile": _('Invalid mobile number'),
                    }
                )
            can_update['mobile'] = validated_data['mobile']
            if User.objects.filter(
                    mobile=validated_data['mobile'],
                    is_active=True,
                    deleted=False,
            ).exclude(
                guid=instance.guid,
            ).exists():
                raise serializers.ValidationError(
                    {
                        "mobile": _("This mobile is already exists")
                    }
                )

        if "gender" in validated_data:
            can_update['gender'] = validated_data['gender']
        if "ascii_name" in validated_data:
            can_update['ascii_name'] = validated_data['ascii_name']
        if "first_name" in validated_data:
            can_update['first_name'] = validated_data['first_name']
        if "last_name" in validated_data:
            can_update['last_name'] = validated_data['last_name']

        return super().update(instance, can_update)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "customer_code":
                instance.customer.customer_code if instance.customer else None,
            "prime_code":
                instance.customer.prime_code if instance.customer else None,
            "username": instance.username,
            "last_login": instance.last_login,
            "user_type": instance.user_type,
            "email": instance.email,
            "mobile": instance.mobile,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "ascii_name": instance.ascii_name,
            "gender": instance.gender,
            "is_active": instance.is_active,
            "deleted": instance.deleted,
            "groups": get_group_name(instance.groups),
        }

    class Meta:
        model = User
        fields = '__all__'


class CreateUserSerializer(serializers.Serializer):
    customer_code = serializers.CharField(
        max_length=255,
        required=False,
    )
    customer_id = serializers.CharField(
        max_length=255,
        required=False,
    )
    password = serializers.CharField(
        max_length=255,
        required=False,
    )
    username = serializers.CharField(
        max_length=255,
        required=True,
    )
    email = serializers.CharField(
        max_length=255,
        required=False,
    )
    mobile = serializers.CharField(
        max_length=255,
        required=False,
    )
    first_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    last_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    ascii_name = serializers.CharField(
        max_length=255,
        required=False,
    )
    gender = serializers.ChoiceField(
        choices=[
            MembershipConfiguration.USER_GENDER[0][0],
            MembershipConfiguration.USER_GENDER[1][0],
        ],
        default=MembershipConfiguration.USER_GENDER[0][0],
    )
    user_type = serializers.ChoiceField(
        choices=[
            MembershipConfiguration.USER_TYPES[0][0],
            MembershipConfiguration.USER_TYPES[1][0],
        ],
        default=MembershipConfiguration.USER_TYPES[0][0],
    )
    group = serializers.ChoiceField(
        required=True,
        choices=[
            Group.FINANCE,
            Group.SALES,
            Group.CUSTOMER_ADMIN,
            Group.CUSTOMER_OPERATOR,
            Group.SUPPORT_ADMIN,
            Group.SUPPORT_OPERATOR,
            Group.PHONE_OPERATOR,
        ],
    )

    def validate(self, attrs):
        if 'password' not in attrs:
            attrs['password'] = Helper.generate_strong_password(12)
        if 'customer_code' in attrs:
            try:
                attrs['customer_id'] = Customer.objects.get(
                    customer_code=attrs['customer_code'],
                ).id
            except Customer.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "customer_code":
                            _("Customer does not exists")
                    }
                )
        if 'username' in attrs:
            if attrs['group'] in (
                    Group.FINANCE,
                    Group.SALES,
                    Group.SUPPORT_ADMIN,
                    Group.SUPPORT_OPERATOR,
                    Group.PHONE_OPERATOR,
            ):
                # No customer is needed
                if User.objects.filter(
                        username=attrs['username'],
                        is_active=True,
                        deleted=False,
                ).exists():
                    raise serializers.ValidationError(
                        {
                            "username": _("This username is already exists")
                        }
                    )
            else:
                if 'customer_code' in attrs:
                    if Customer.objects.filter(
                            customer_code=attrs['customer_code'],
                            users__username=attrs['username'],
                            users__is_active=True,
                            users__deleted=False,
                    ).exists():
                        raise serializers.ValidationError(
                            {
                                "username":
                                    _("Duplicate username for this customer")
                            }
                        )
                else:
                    raise serializers.ValidationError(
                        {
                            'customer_code': _("This field is required")
                        }
                    )
                attrs.pop('customer_code')

        if self.context:
            error = {}
            if 'mobile' not in attrs:
                error['mobile'] = _("This field is required")
            if 'email' not in attrs:
                error['email'] = _("This field is required")
            if error:
                raise serializers.ValidationError(error)

        if 'mobile' in attrs:
            if not Helper.is_mobile_number(
                    attrs['mobile']
            ):
                raise serializers.ValidationError(
                    {
                        "mobile": _('Invalid mobile number'),
                    }
                )
            if User.objects.filter(
                    mobile=attrs['mobile'],
                    is_active=True,
                    deleted=False,
            ).exists():
                raise serializers.ValidationError(
                    {
                        "mobile": _("This mobile is already exists")
                    }
                )

        if 'email' in attrs:
            if not Helper.is_email(
                    attrs['email']
            ):
                raise serializers.ValidationError(
                    {
                        "email": _('Invalid email'),
                    }
                )
            if User.objects.filter(
                    email=attrs['email'],
                    is_active=True,
                    deleted=False,
            ).exists():
                raise serializers.ValidationError(
                    {
                        "email": _("This email is already exists")
                    }
                )

        group_name = attrs.pop("group")
        if group_name:
            try:
                attrs['group'] = GroupModel.objects.get(
                    name=group_name,
                ).id
            except GroupModel.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "group": _("Group does not exists")
                    }
                )

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserGenerateTokenSerializer(serializers.Serializer):
    prime_code = serializers.IntegerField(
        allow_null=True,
        required=False,
    )
    username = serializers.CharField(max_length=255, required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserLoginSerializer(serializers.Serializer):
    prime_code = serializers.CharField(
        max_length=255,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    username = serializers.CharField(max_length=255, required=True)
    password = serializers.CharField(max_length=255, required=True)
    remember_me = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserEmpowerSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserRenewPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, max_length=128)
    new_password1 = serializers.CharField(required=True, max_length=128)
    new_password2 = serializers.CharField(required=True, max_length=128)

    def validate(self, attrs):
        if attrs['new_password1'] and attrs['new_password2'] and \
                attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {
                    "new_password1": _("New password does not match")
                }
            )
        if Helper.is_password_weak(attrs['new_password1']):
            raise serializers.ValidationError({
                "new_password1": _("The new password is weak")
            })

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserRecoverPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, max_length=1024)
    new_password1 = serializers.CharField(required=True, max_length=128)
    new_password2 = serializers.CharField(required=True, max_length=128)

    def validate(self, attrs):
        if attrs['new_password1'] and attrs['new_password2'] and \
                attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {
                    "new_password1": _("New password does not match")
                }
            )
        if Helper.is_password_weak(attrs['new_password1']):
            raise serializers.ValidationError({
                "new_password1": _("The new password is weak")
            })

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserSetPasswordSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(required=True, max_length=128)
    new_password2 = serializers.CharField(required=True, max_length=128)

    def validate(self, attrs):
        if attrs['new_password1'] and attrs['new_password2'] and \
                attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {
                    "new_password1": _("New password does not match")
                }
            )
        if Helper.is_password_weak(attrs['new_password1']):
            raise serializers.ValidationError({
                "new_password1": _("The new password is weak")
            })

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
