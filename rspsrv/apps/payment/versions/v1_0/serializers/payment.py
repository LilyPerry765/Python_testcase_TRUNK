# --------------------------------------------------------------------------
# This should deprecate
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - payment.py
# Created at 2020-6-16,  8:58:12
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

from django.utils.translation import gettext as _
from rest_framework import serializers

from rspsrv.apps.file.versions.v1_0.services import FileService
from rspsrv.apps.invoice.versions.v1_0.config import InvoiceConfiguration
from rspsrv.apps.payment.versions.v1_0.config.config import (
    Payment as PaymentConfig, PaymentConfiguration,
)


class PaymentSerializer(serializers.Serializer):
    is_hybrid = serializers.BooleanField(
        default=False,
        required=False,
    )
    subscription_code = serializers.CharField(
        max_length=256,
        required=False,
    )
    invoice_id = serializers.CharField(
        max_length=256,
        required=True,
    )
    invoice_type = serializers.CharField(
        max_length=128,
        required=True,
    )
    files_id = serializers.ListField(
        child=serializers.CharField(max_length=512),
        default=[],
        required=False,
        allow_empty=True,
        allow_null=True,
    )
    payment_gateway = serializers.ChoiceField(
        choices=PaymentConfig.gateways_choices(return_list=True),
        required=False,
    )
    description = serializers.CharField(
        max_length=512,
        default='',
        required=False,
        allow_blank=True,
    )

    def validate(self, fields):
        credit_type = InvoiceConfiguration.InvoiceTypes.CREDIT_INVOICE
        credit_gateway = PaymentConfiguration.Gateway.CREDIT
        offline_gateway = PaymentConfiguration.Gateway.OFFLINE
        if fields['invoice_type'] == credit_type and \
                fields['payment_gateway'] == credit_gateway:
            raise serializers.ValidationError(
                {
                    'payment_gateway': _(
                        "Invalid payment gateway for credit invoice",
                    )
                }
            )
        if "files_id" not in fields and \
                fields['payment_gateway'] != offline_gateway:
            fields["files_id"] = []
        elif "files_id" in fields and len(fields['files_id']) == 0 and \
                fields['payment_gateway'] == offline_gateway:
            raise serializers.ValidationError(
                {
                    'files': _(
                        "offline payments must have attachments",
                    )
                }
            )
        else:
            for file_id in fields['files_id']:
                if not FileService.check_file_existence(file_id):
                    raise serializers.ValidationError(
                        {
                            'files': _(
                                "one or more files does not exists",
                            )
                        }
                    )

        return fields

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PaymentApprovalSerializer(serializers.Serializer):
    approved = serializers.BooleanField(required=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
