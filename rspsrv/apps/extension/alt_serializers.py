from django.utils.translation import gettext as _
from rest_framework import serializers

from rspsrv.apps.extension.models import (
    Extension,
    ExtensionNumber,
)
from rspsrv.tools.utility import Helper


class ExtensionSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(ExtensionSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Extension
        fields = '__all__'


class ExtensionNumberSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(ExtensionNumberSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = ExtensionNumber
        fields = '__all__'


class ExtensionUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        if Helper.is_password_weak_extension(attrs['password']):
            raise serializers.ValidationError({
                'password': _("Password is weak")
            })

        return attrs

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
