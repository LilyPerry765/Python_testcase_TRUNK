# --------------------------------------------------------------------------
# This app and CGG have duplications of knowledge, merge them in future to
# be DRY
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - models.py
# Created at 2020-10-26,  17:1:17
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import uuid

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext as _

from rspsrv.apps.call.apps.base import CallApplicationType
from rspsrv.apps.call.call_control.channel import ChannelContext
from rspsrv.apps.membership.models import (
    Customer,
    User,
)
from rspsrv.apps.subscription.manager import SubscriptionManager
from rspsrv.tools import api_exceptions
from rspsrv.tools.utility import RespinaBaseModel

ROUTE_CHOICE = (
    (CallApplicationType.end, 'End Call'),
    (CallApplicationType.EXTENSION, 'Extension'),
)
# Sync this with CGG
SUBSCRIPTION_TYPES = (
    ('postpaid', _('Postpaid')),
    ('prepaid', _('Prepaid')),
    ('unlimited', _('Unlimited')),
)

DestinationTypeChoices = (
    ('cell', 'Cellphone'),
    ('land', 'Landlines')
)


class Subscription(RespinaBaseModel):
    number = models.CharField(
        max_length=64,
        db_index=True,
    )
    customer = models.ForeignKey(
        Customer,
        related_name='subscriptions',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    operator = models.OneToOneField(
        User,
        null=True,
        blank=True,
        related_name='subscription',
        on_delete=models.SET_NULL,
    )
    subscription_code = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=False,
        db_index=True,
    )
    subscription_type = models.CharField(
        max_length=128,
        null=False,
        blank=False,
        db_index=True,
        choices=SUBSCRIPTION_TYPES,
        default=SUBSCRIPTION_TYPES[0][0],
    )
    activation = models.BooleanField(
        default=True
    )
    international_call = models.BooleanField(
        default=False
    )
    destination_type = models.CharField(
        max_length=64,
        choices=ROUTE_CHOICE,
    )
    destination_number = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    destination_type_off = models.CharField(
        max_length=64,
        choices=ROUTE_CHOICE,
    )
    destination_number_off = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    destination_type_in_list = models.CharField(
        max_length=64,
        choices=ROUTE_CHOICE,
        default=CallApplicationType.end,
        null=True,
        blank=True
    )
    destination_number_in_list = models.CharField(
        max_length=128, null=True,
        blank=True,
    )
    max_call_concurrency = models.PositiveIntegerField(
        default=1,
    )
    allow_inbound = models.BooleanField(
        default=True,
    )
    allow_outbound = models.BooleanField(
        default=True,
    )
    is_allocated = models.BooleanField(
        default=True,
        db_index=True,
    )
    outbound_prefix = models.CharField(
        max_length=2,
        default=9
    )
    outbound_min_length = models.IntegerField()
    latitude = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        default=None
    )
    longitude = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        default=None
    )
    ip = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        default=None
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
    )
    objects = SubscriptionManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.number)

    def target_number_is_outbound(self, target_number):
        return len(str(target_number)) >= self.outbound_min_length \
               or str(target_number).startswith(self.outbound_prefix)

    def outbound_number_regulation(self, target_number):
        if len(str(target_number)) <= self.outbound_min_length and str(
                target_number).startswith(self.outbound_prefix):
            return str(target_number)[len(self.outbound_prefix):]
        return target_number

    def channel_is_outbound(self, channel):
        return self.target_number_is_outbound(
            target_number=channel.destination_number)

    def call_is_outbound(self, channel=None, target_number=None):
        if channel:
            return self.channel_is_outbound(channel)
        elif target_number:
            return self.target_number_is_outbound(target_number)

    def target_number_is_allowed(self, target_number):
        if self.target_number_is_outbound(target_number):
            return self.allow_outbound
        return True

    def call_is_allowed(self, channel):
        if channel.context == ChannelContext.INBOUND:
            return self.allow_inbound
        return self.target_number_is_allowed(channel.destination_number)

    def get_destination(self):
        return self.destination_type, self.destination_number

    @property
    def prime_code(self):
        if self.customer:
            return self.customer.prime_code

        return None

    @property
    def extension(self):
        return self.subscription_extension

    @property
    def customer_code(self):
        if self.customer:
            return self.customer.customer_code

        return None

    def save(self):
        if int(self.max_call_concurrency) <= 0:
            raise api_exceptions.APIException(
                _("Concurrency can not be less than 1!")
            )
        super(Subscription, self).save()


class MaxCallConcurrencyHistory(RespinaBaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    subscription = models.ForeignKey(
        Subscription,
        related_name='call_concurrency_history',
        on_delete=models.PROTECT,
    )
    old_value = models.PositiveIntegerField()
    new_value = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


@receiver(
    pre_save,
    sender=Subscription,
)
def pre_save_call_concurrency(
        sender,
        instance,
        *args,
        **kwargs
):
    try:
        old = Subscription.objects.get(
            id=instance.id,
        )
    except Subscription.DoesNotExist:
        return
    if old.max_call_concurrency != instance.max_call_concurrency:
        history = MaxCallConcurrencyHistory()
        history.old_value = old.max_call_concurrency
        history.new_value = instance.max_call_concurrency
        history.subscription = instance
        history.save()
