from django.utils.translation import gettext as _
from rest_framework import serializers

from rspsrv.apps.extension.models import EXTENSION_STATUS_CHOICES
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.utility import Helper


class SubscriptionCodeSerializer(serializers.Serializer):
    subscription_code = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionAssignSerializer(serializers.Serializer):
    assign_to = serializers.IntegerField(
        required=True,
        allow_null=True,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionUpdateSerializer(serializers.Serializer):
    max_call_concurrency = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    allow_inbound = serializers.BooleanField(
        required=False,
    )
    allow_outbound = serializers.BooleanField(
        required=False,
    )
    activation = serializers.BooleanField(
        required=False,
    )
    international_call = serializers.BooleanField(
        required=False,
    )
    password = serializers.CharField(
        required=False,
    )
    status = serializers.CharField(
        required=False,
    )
    forward_to = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        if 'status' in attrs and attrs['status']:
            if attrs['status'] not in [s[0] for s in EXTENSION_STATUS_CHOICES]:
                raise serializers.ValidationError({
                    'status': _("Not a valid choice")
                })
            if attrs['status'] == EXTENSION_STATUS_CHOICES[0][0] and not (
                    'forward_to' in attrs and attrs['forward_to']
            ):
                raise serializers.ValidationError({
                    'forward_to': _(
                        "Use a phone number when choosing forward status"
                    )
                })
            if attrs['status'] != EXTENSION_STATUS_CHOICES[0][0]:
                attrs['forward_to'] = ""
        if 'forward_to' in attrs and attrs['forward_to']:
            if not Helper.is_valid_number(attrs['forward_to']):
                raise serializers.ValidationError({
                    'forward_to': _("Must be a valid number")
                })
        if 'password' in attrs and attrs['password']:
            if Helper.is_password_weak_extension(attrs['password']):
                raise serializers.ValidationError({
                    'password': _("Password is weak")
                })

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionAutoPaySerializer(serializers.Serializer):
    auto_pay = serializers.BooleanField(
        required=True,
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id',
            'number',
            'subscription_code',
            'subscription_type',
            'prime_code',
            'customer_code',
            'operator_id',
            'activation',
            'is_allocated',
            'allow_inbound',
            'allow_outbound',
            'international_call',
            'max_call_concurrency',
            'destination_type',
            'destination_number',
            'destination_type_off',
            'destination_number_off',
            'destination_type_in_list',
            'destination_number_in_list',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'number',
            'customer_id',
            'operator_id',
            'prime_code',
            'customer_code',
            'client',
            'base_balance',
            'used_balance',
            'destination_type',
            'destination_type_off',
            'subscription_code',
            'subscription_type',
            'created_at',
        ]

    def to_representation(self, instance):
        instance_dict = dict(super().to_representation(instance))
        if self.context and instance_dict['subscription_code'] in self.context:
            subscription_detail = self.context[
                instance_dict['subscription_code']
            ]
            instance_dict.update({
                'credit': subscription_detail['credit'],
                'auto_pay': subscription_detail[
                    'auto_pay'
                ],
                'latest_paid_at': subscription_detail[
                    'latest_paid_at'
                ],
                'deallocated_at': subscription_detail[
                    'deallocated_at'
                ],
                'used_balance_postpaid': subscription_detail[
                    'used_balance_postpaid'
                ],
                'current_balance_postpaid': subscription_detail[
                    'current_balance_postpaid'
                ],
                'base_balance_postpaid': subscription_detail[
                    'base_balance_postpaid'
                ],
                'base_balance_prepaid': subscription_detail[
                    'base_balance_prepaid'
                ],
                'used_balance_prepaid': subscription_detail[
                    'used_balance_prepaid'
                ],
                'current_balance_prepaid': subscription_detail[
                    'current_balance_prepaid'
                ]
            })

        if hasattr(instance, 'extension'):
            instance_dict.update({
                "extension": {
                    "password": instance.extension.password,
                    "status": instance.extension.status,
                    "forward_to": instance.extension.forward_to,
                }
            })
        else:
            instance_dict.update({
                "extension": {
                    "password": None,
                    "status": None,
                    "forward_to": None,
                }
            })

        return instance_dict


class SubscriptionExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id',
            'number',
            'subscription_code',
            'subscription_type',
            'prime_code',
            'customer_code',
            'operator_id',
            'activation',
            'is_allocated',
            'allow_inbound',
            'allow_outbound',
            'international_call',
            'max_call_concurrency',
            'destination_type',
            'destination_number',
            'destination_type_off',
            'destination_number_off',
            'destination_type_in_list',
            'destination_number_in_list',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'number',
            'customer_id',
            'operator_id',
            'prime_code',
            'customer_code',
            'client',
            'base_balance',
            'used_balance',
            'max_call_concurrency',
            'allow_inbound',
            'allow_outbound',
            'subscription_code',
            'subscription_type',
            'created_at',
        ]

    def to_representation(self, instance):
        subscription_detail = self.context[instance.subscription_code]

        return {
            _("id"): Helper.to_string_for_export(
                instance.id
            ),
            _("prime code"): Helper.to_string_for_export(
                instance.prime_code
            ),
            _("subscription code"): Helper.to_string_for_export(
                instance.subscription_code
            ),
            _("subscription type"): Helper.to_string_for_export(
                Helper.translator(instance.subscription_type)
            ),
            _("main number"): Helper.to_string_for_export(
                instance.number
            ),
            _("credit"): Helper.to_string_for_export(
                subscription_detail['credit']
            ),
            _("max call concurrency"): Helper.to_string_for_export(
                instance.max_call_concurrency
            ),
            _("activation"): Helper.to_string_for_export(
                instance.activation,
                True,
            ),
            _("allow inbound"): Helper.to_string_for_export(
                instance.allow_inbound,
                True,
            ),
            _("allow outbound"): Helper.to_string_for_export(
                instance.allow_outbound,
                True,
            ),
            _("international call"): Helper.to_string_for_export(
                instance.international_call,
                True,
            ),
            _("auto pay"): Helper.to_string_for_export(
                subscription_detail['auto_pay'],
                True,
            ),
            _("base balance postpaid"): subscription_detail[
                'base_balance_postpaid'
            ],
            _("current balance postpaid"): subscription_detail[
                'current_balance_postpaid'
            ],
            _("used balance postpaid"): subscription_detail[
                'used_balance_postpaid'
            ],
            _("base balance prepaid"): subscription_detail[
                'base_balance_prepaid'
            ],
            _("current balance prepaid"): subscription_detail[
                'current_balance_prepaid'
            ],
            _("used balance prepaid"): subscription_detail[
                'used_balance_prepaid'
            ],
            _("created at"): Helper.to_jalali_date(
                instance.created_at,
            ),
        }
