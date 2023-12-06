from django.db import models
from django.utils import timezone

from rspsrv.apps.endpoint.manager import (
    EndpointManager, BrandManager,
    EndpointOptionManager, BrandOptionManager,
)
from rspsrv.apps.endpoint.serilaizers import (
    BrandSerializer,
    EndpointSerializer,
)
from rspsrv.apps.membership.models import User
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.utility import RespinaBaseModel


class PhoneStatus(object):
    Online = 'online'
    Offline = 'offline'
    DND = 'dnd'
    Forward = 'forward'


PHONE_STATUS_CHOICE = (
    (PhoneStatus.Online, 'Online'),
    (PhoneStatus.Offline, 'Offline'),
    (PhoneStatus.DND, 'DND'),
    (PhoneStatus.Forward, 'Forward'),
)


def get_brand_upload_path(instance, filename):
    extension = filename.split('.')[1]
    name = '.'.join([instance.name.replace(' ', '_'), extension])
    return 'brand/%s' % name


class Brand(RespinaBaseModel):
    name = models.CharField(max_length=128, unique=True)
    extra_options = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    objects = BrandManager()
    serializer = BrandSerializer

    def __str__(self):
        return self.name


class Endpoint(RespinaBaseModel):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
    )
    mac_address = models.CharField(max_length=12, unique=True)
    enabled = models.BooleanField(default=True)
    subscription = models.ForeignKey(
        Subscription,
        related_name='endpoints',
        on_delete=models.PROTECT,
    )
    extra_options = models.BooleanField(default=False)
    status = models.CharField(max_length=64, choices=PHONE_STATUS_CHOICE,
                              default=PhoneStatus.Offline, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EndpointManager()
    serializer = EndpointSerializer

    def save(self, *args, **kwargs):
        self.mac_address = self.mac_address.upper()
        super(Endpoint, self).save(*args, **kwargs)

    def __str__(self):
        return ' '.join([
            self.mac_address,
            self.brand.name,
            self.subscription.number,
        ])


class EndpointOption(models.Model):
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=128)
    endpoint = models.ForeignKey(
        Endpoint,
        related_name='option_list',
        on_delete=models.PROTECT,
    )
    objects = EndpointOptionManager()

    def __str__(self):
        return self.key


class BrandOption(models.Model):
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=128)
    brand = models.ForeignKey(
        Brand,
        related_name='option_list',
        on_delete=models.PROTECT,
    )
    objects = BrandOptionManager()

    def __str__(self):
        return self.key
