import logging

from django.utils.translation import gettext as _
from rest_framework import serializers, exceptions

from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class ProductEmpowerSerializer(serializers.Serializer):
    inbound = serializers.BooleanField(default=True)
    outbound = serializers.BooleanField(default=True)
    activation = serializers.BooleanField(default=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ProductUpdateSerializer(serializers.Serializer):
    base_balance = serializers.IntegerField(required=False, allow_null=True)
    ip = serializers.CharField(required=False, allow_null=True)
    latitude = serializers.CharField(required=False, allow_null=True)
    longitude = serializers.CharField(required=False, allow_null=True)
    max_call_concurrency = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    def validate_max_call_concurrency(self, value):
        if value <= 0:
            raise exceptions.ValidationError(
                detail={
                    'max_call_concurrency': _("Must be a positive integer")
                }
            )

        return value

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ProductCreateSerializer(serializers.Serializer):
    is_prepaid = serializers.BooleanField(default=False)
    has_pro = serializers.BooleanField(default=False)
    product_id = serializers.CharField()
    customer_id = serializers.CharField()
    package_id = serializers.CharField(
        allow_null=True,
        default=None,
    )
    main_number = serializers.CharField(
        max_length=20,
        min_length=8
    )
    base_balance = serializers.IntegerField()
    ip = serializers.CharField()
    latitude = serializers.CharField()
    longitude = serializers.CharField()
    max_call_concurrency = serializers.IntegerField()

    def validate_main_number(self, value):
        validated_number = Helper.normalize_number(
            value
        )
        if validated_number:
            return validated_number

        raise serializers.ValidationError(
            _("Should be a number (Could start with or without a plus sign)")
        )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def to_representation(self, instance):
        instance = dict(instance)
        instance['customer_code'] = instance['customer_id']

        return {
            "package_id": instance["package_id"],
            "is_prepaid": instance["is_prepaid"],
            "subscription_code": instance["product_id"],
            "customer_code": instance["customer_id"],
            "number": instance["main_number"],
            "has_pro": instance["has_pro"],
            "base_balance": instance["base_balance"],
            "ip": instance["ip"],
            "latitude": instance["latitude"],
            "longitude": instance["longitude"],
            "max_call_concurrency": instance["max_call_concurrency"],
        }


class SubscriptionCreateSerializer(serializers.Serializer):
    package_id = serializers.CharField(default=None, allow_null=True)
    subscription_code = serializers.CharField(required=True)
    number = serializers.CharField(required=True)
    base_balance = serializers.CharField(required=True)
    customer_id = serializers.CharField(required=True)
    max_call_concurrency = serializers.CharField(required=True)
    destination_number = serializers.CharField(required=True)
    latitude = serializers.CharField(required=True)
    longitude = serializers.CharField(required=True)
    ip = serializers.CharField(required=True)

    def validate(self, attrs):
        number = attrs['number']
        subscription_code = attrs['subscription_code']
        number = Helper.normalize_number(
            number
        )
        if not number:
            raise serializers.ValidationError(
                _(
                    "Should be a number (Could start with or without a plus "
                    "sign)",
                )
            )
        if Subscription.objects.filter(
                number=number,
                is_allocated=True,
        ).exists():
            raise exceptions.ValidationError(
                detail=_('Main number is already exists')
            )

        if Subscription.objects.filter(
                subscription_code=subscription_code,
        ).exists():
            raise exceptions.ValidationError(
                detail={
                    'subscription_code': _(
                        'Subscription code is already exists',
                    )
                }
            )

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
