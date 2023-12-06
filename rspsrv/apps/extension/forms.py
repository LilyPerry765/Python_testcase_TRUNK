import logging

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from rspsrv.apps.call.apps.base import CallApplicationType
from rspsrv.apps.extension.models import (
    Extension,
    EXTENSION_STATUS_CHOICES,
    ExtensionNumber,
)
from rspsrv.tools.forms import BaseRespinaModelForm, BaseRespinaForm

logger = logging.getLogger("common")


class ExtensionModelForm(BaseRespinaModelForm):
    extension_number = forms.CharField(required=True)

    class Meta:
        model = Extension

        fields = [
            'has_pro',
            'customer',
            'endpoint',
            'callerid',
            'web_enabled',
            'external_call_enable',
            'record_all',
            'show_contacts',
            'ring_seconds',
            'call_waiting',
            'password',
            'inbox_enabled',
            'enabled',
            'international_call',
            'subscription',
            'destination_type_off',
            'destination_number_off',
            'destination_type_no_answer',
            'destination_number_no_answer',
            'destination_type_in_list',
            'destination_number_in_list'
        ]

    def clean_extension_number(self):
        extension_number = self.cleaned_data['extension_number']

        if ExtensionNumber.objects.filter(number=extension_number).exists():
            if not self.instance.pk:
                raise ValidationError(
                    'Duplicate extension_number',
                    code='duplicate_extension_number',
                )

            if Extension.objects.filter(
                    ~Q(id=self.instance.pk),
                    extension_number__number=extension_number,
            ).exists():
                raise ValidationError(
                    'Duplicate extension_number',
                    code='duplicate_extension_number',
                )

        return extension_number

    def save(self, commit=True):
        extension = super(ExtensionModelForm, self).save(commit=False)
        is_update_request = False
        previous_number = None
        previous_password = None

        if self.instance.pk:
            previous_number = extension.extension_number.number
            previous_password = extension.password
            extension.extension_number.number = self.cleaned_data['extension_number']
            extension.password = self.cleaned_data['password']
            extension.extension_number.save()
            is_update_request = True

        else:
            extension.extension_number = ExtensionNumber.objects.create(
                number=self.cleaned_data['extension_number'],
                type=CallApplicationType.EXTENSION
            )

        if commit:
            extension.save(
                is_update_request=is_update_request,
                previous_number=previous_number,
                previous_password=previous_password
            )

        return extension


class ExtensionStatusForm(BaseRespinaForm):
    status = forms.CharField(required=True)
    forward_to = forms.CharField(required=False)

    def status_clean(self):
        status = self.cleaned_data['status']

        found = False
        for choice in EXTENSION_STATUS_CHOICES:
            if choice[0] == status:
                found = True
                break

        if not found:
            raise ValidationError('Invalid status choice')

        return status
