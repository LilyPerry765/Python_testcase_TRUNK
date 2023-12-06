import json

from django import forms
from django.core.exceptions import ValidationError

from rspsrv.apps.endpoint.models import Endpoint, EndpointOption
from rspsrv.tools.forms import BaseRespinaModelForm


class EndpointModelForm(BaseRespinaModelForm):
    brand_options = forms.Textarea()

    class Meta:
        model = Endpoint
        fields = [
            'brand',
            'mac_address',
            'enabled',
            'subscription',
            'extra_options',
            'status',
            'ip_address',
        ]

    def save(self, commit=True):
        new_endpoint = super(EndpointModelForm, self).save(commit=False)

        if commit:
            new_endpoint.save()

        brand_options = self.cleaned_data.get('brand_options', [])
        for option in brand_options:
            EndpointOption.objects.create(
                key=option,
                value=brand_options[option],
                endpoint=new_endpoint
            )

        return new_endpoint

    def clean_mac_address(self):
        mac_address = self.cleaned_data['mac_address']
        if Endpoint.objects.filter(mac_address=mac_address).exists():
            if not self.instance.id:
                raise ValidationError('Duplicate mac_address',
                                      'duplicate_mac_address')
            if Endpoint.objects.exclude(id=self.instance.id).filter(
                    mac_address=mac_address).exists():
                raise ValidationError('Duplicate mac_address',
                                      'duplicate_mac_address')

        return mac_address

    def options_clean(self):
        brand_options = self.cleaned_data['brand_options']
        if brand_options:
            try:
                brand_options = json.loads(brand_options)
            except Exception:
                raise ValidationError('Invalid json')

        return brand_options
