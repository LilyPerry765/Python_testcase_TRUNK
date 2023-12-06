from rest_framework import serializers

from rspsrv.apps.membership.models import Customer
from rspsrv.apps.mis.versions.v1_0.services.mis import MisService


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id',
            'customer_code',
            'is_active',
            'deleted',
            'created_at',
            'prime_code',
        ]


class CustomerMergedSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        try:
            info = MisService.get_client_info(
                subscription_code=
                instance.subscriptions.all()[0].subscription_code,
            )
        except Exception:
            info = None

        return {
            'id': instance.id,
            'customer_code': instance.customer_code,
            'is_active': instance.is_active,
            'deleted': instance.deleted,
            'created_at': instance.created_at,
            'prime_code': instance.prime_code,
            'credit': self.context[str(instance.id)]['credit'],
            'info': info,
        }

    class Meta:
        model = Customer
        fields = '__all__'
