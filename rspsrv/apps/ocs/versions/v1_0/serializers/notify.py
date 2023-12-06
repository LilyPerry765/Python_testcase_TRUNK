from rest_framework import serializers


class NotifyInvoiceSerializer(serializers.Serializer):
    customer_code = serializers.CharField(required=True)
    subscription_code = serializers.CharField(required=True)
    number = serializers.CharField(required=True)
    cause = serializers.CharField(required=False)
    invoice_id = serializers.CharField(required=True)
    total_cost = serializers.IntegerField(required=True)
    auto_payed = serializers.BooleanField(default=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class NotifySubscriptionSerializer(serializers.Serializer):
    customer_code = serializers.CharField(required=True)
    subscription_code = serializers.CharField(required=True)
    number = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
