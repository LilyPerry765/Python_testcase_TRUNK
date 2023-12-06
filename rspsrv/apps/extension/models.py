import logging

from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from rspsrv.apps.call.apps.base import CallApplicationType
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.call_pool import LI
from rspsrv.apps.call.call_control.iri import SupplementaryIRIReport
from rspsrv.apps.call.call_control.spy import Interception
from rspsrv.apps.endpoint.models import Endpoint
from rspsrv.apps.extension.manager import (
    ExtensionManger,
)
from rspsrv.apps.extension.serilaizers import (
    ExtensionSerializer,
    ExtensionNumberSerializer,
)
from rspsrv.apps.membership.models import Customer
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.asterisk_registration import AsteriskDatabase
from rspsrv.tools.kazoo_registration import KazooKamailioDatabase
from rspsrv.tools.utility import BaseChoice, RespinaBaseModel

logger = logging.getLogger("common")


class ExtensionStatus(object):
    FORWARD = BaseChoice(value='forward', label='Forward Call')
    DISABLE = BaseChoice(value='disable', label='Disable')
    AVAILABLE = BaseChoice(value='available', label='Available')
    OFFLINE = BaseChoice(value='offline', label='Offline')
    DND = BaseChoice(value='dnd', label='Do not disturb')


EXTENSION_STATUS_CHOICES = (
    (ExtensionStatus.FORWARD.Value, ExtensionStatus.FORWARD.Label),
    (ExtensionStatus.DISABLE.Value, ExtensionStatus.DISABLE.Label),
    (ExtensionStatus.AVAILABLE.Value, ExtensionStatus.AVAILABLE.Label),
    (ExtensionStatus.OFFLINE.Value, ExtensionStatus.OFFLINE.Label),
    (ExtensionStatus.DND.Value, ExtensionStatus.DND.Label),
)

EXTENSION_NUMBER_APP_CHOICES = (
    (CallApplicationType.INBOX, "Extension's Inbox"),
    (CallApplicationType.QUEUE, "Call Queue"),
    (CallApplicationType.RECEPTIONIST, "Digital Receptionist"),
    (CallApplicationType.EXTENSION, "Extension"),
    (CallApplicationType.RING_GROUP, "Ring Group"),
    (CallApplicationType.FAX, "Fax"),
)

TYPE_OFF_ROUTE_CHOICES = (
    (CallApplicationType.end, 'End Call'),
    (CallApplicationType.EXTENSION, 'Connect to extension'),
    (CallApplicationType.INBOX, 'Voice mailbox for extension'),
    (CallApplicationType.RECEPTIONIST, 'Connect to digital receptionist'),
    (CallApplicationType.QUEUE, 'Connect to queue'),
    (CallApplicationType.RING_GROUP, 'Connect to ring group'),
    (CallApplicationType.EXTERNAL, 'Forward to outside number'),
)

CONDITIONAL_LIST_ROUTE_CHOICES = (
    (CallApplicationType.end, 'End Call'),
    (CallApplicationType.EXTENSION, 'Connect to extension'),
    (CallApplicationType.INBOX, 'Voice mailbox for extension'),
    (CallApplicationType.RECEPTIONIST, 'Connect to digital receptionist'),
    (CallApplicationType.QUEUE, 'Connect to queue'),
    (CallApplicationType.RING_GROUP, 'Connect to ring group'),
    (CallApplicationType.EXTERNAL, 'Forward to outside number'),
)

NO_ANSWER_ROUTE_CHOICES = (
    (CallApplicationType.end, 'End Call'),
    (CallApplicationType.EXTENSION, 'Connect to extension'),
    (CallApplicationType.INBOX, 'Voice mailbox for extension'),
    (CallApplicationType.RECEPTIONIST, 'Connect to digital receptionist'),
    (CallApplicationType.QUEUE, 'Connect to queue'),
    (CallApplicationType.RING_GROUP, 'Connect to ring group')
)


class ExtensionOnTimeoutAction(object):
    No = BaseChoice(label='No', value='no')
    Email = BaseChoice(label='Send Email', value='email')
    EmailAndMessage = BaseChoice(
        label='Send Email with Message as an Attachment',
        value='emailandmessage',
    )
    EmailXorMessage = BaseChoice(
        label='Send Email with Message amd delete from Inbox',
        value='emailxormessage',
    )


EXTENSION_ON_TIMEOUT_ACTION_CHOICES = (
    (ExtensionOnTimeoutAction.No.Value, ExtensionOnTimeoutAction.No.Label),
    (ExtensionOnTimeoutAction.Email.Value,
     ExtensionOnTimeoutAction.Email.Label),
    (ExtensionOnTimeoutAction.EmailAndMessage.Value,
     ExtensionOnTimeoutAction.EmailAndMessage.Label),
    (ExtensionOnTimeoutAction.EmailXorMessage.Value,
     ExtensionOnTimeoutAction.EmailXorMessage.Label),
)


class ExtensionNumber(models.Model):
    number = models.CharField(
        max_length=32,
        unique=True,
    )
    did = models.CharField(max_length=32, unique=True, null=True, blank=True)
    type = models.CharField(
        max_length=32,
        choices=EXTENSION_NUMBER_APP_CHOICES,
    )
    serializer = ExtensionNumberSerializer

    def __str__(self):
        return "%s (%s)" % (self.number, self.type)


class Extension(RespinaBaseModel):
    customer = models.ForeignKey(
        Customer,
        related_name='extensions',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    password = models.CharField(max_length=256)
    callerid = models.CharField(max_length=128)
    endpoint = models.ForeignKey(
        Endpoint,
        null=True,
        blank=True,
        related_name='extensions',
        on_delete=models.PROTECT,
    )
    extension_number = models.OneToOneField(
        ExtensionNumber,
        related_name='extension',
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        max_length=32,
        choices=EXTENSION_STATUS_CHOICES,
        default=ExtensionStatus.AVAILABLE.Value,
    )
    web_enabled = models.BooleanField(default=True)
    external_call_enable = models.BooleanField(default=False)
    record_all = models.BooleanField(default=True)
    show_contacts = models.BooleanField(default=True)
    ring_seconds = models.IntegerField(default=40)
    inbox_enabled = models.BooleanField(default=True)
    has_pro = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    international_call = models.BooleanField(
        verbose_name='International Call Access',
        default=False,
    )
    subscription = models.OneToOneField(
        Subscription,
        null=True,
        blank=True,
        related_name='subscription_extension',
        on_delete=models.PROTECT,
    )
    destination_type_off = models.CharField(
        max_length=64,
        choices=TYPE_OFF_ROUTE_CHOICES,
        verbose_name='Type of Destination (closed)',
        default=CallApplicationType.end
        , null=True,
        blank=True,
    )
    destination_number_off = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='Destination Number (closed)'
    )
    destination_type_no_answer = models.CharField(
        max_length=64,
        choices=NO_ANSWER_ROUTE_CHOICES,
        verbose_name='Type of Destination on No Answer',
        default=CallApplicationType.end,
        null=True,
        blank=True,
    )
    destination_number_no_answer = models.CharField(
        max_length=128, null=True,
        blank=True,
        verbose_name='Destination Number on No Answer',
    )
    destination_type_in_list = models.CharField(
        max_length=64,
        choices=CONDITIONAL_LIST_ROUTE_CHOICES,
        verbose_name='Type of Destination In Conditional List',
        default=CallApplicationType.end,
        null=True,
        blank=True,
    )
    destination_number_in_list = models.CharField(
        max_length=128, null=True,
        blank=True,
        verbose_name='Destination Number In Conditional List'
    )
    forward_to = models.CharField(
        max_length=128,
        verbose_name='Forward To',
        null=True, blank=True,
    )
    call_waiting = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ExtensionManger()
    serializer = ExtensionSerializer
    webapp_type = 'extension'

    @property
    def prime_code(self):
        if self.customer:
            return self.customer.prime_code

        return None

    @property
    def customer_code(self):
        if self.customer:
            return self.customer.customer_code

        return None

    def __init__(self, *args, **kwargs):
        super(Extension, self).__init__(*args, **kwargs)
        self.__previous_status = self.status
        self.__previous_call_waiting = self.call_waiting

    def __str__(self):
        return ' '.join([self.callerid, str(self.extension_number.number)])

    def set_status(self, status):
        self.status = status
        self.save()

    # LI :: HI2
    def send_cfu_iri_report(self, supps_action):
        li_data = Interception.check_for_spy(self.subscription.number)
        if li_data:
            for d in li_data:
                LI.increase_cin()

                iri = SupplementaryIRIReport(
                    target_number=self.subscription.number,
                    li_data=d,
                    supps_type={
                        'service_action': supps_action,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.CFU,
                        'party_number': self.subscription.number,
                    },
                )
                iri.send_report()

    # LI :: HI2
    def send_cw_iri_report(self, supps_action):
        li_data = Interception.check_for_spy(self.subscription.number)
        if li_data:
            for d in li_data:
                LI.increase_cin()

                iri = SupplementaryIRIReport(
                    target_number=self.subscription.number,
                    li_data=d,
                    supps_type={
                        'service_action': supps_action,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.CW,
                        'party_number': self.subscription.number,
                    },
                )
                iri.send_report()

    def save(
            self,
            is_update_request=False,
            previous_number=None,
            previous_password=None,
            **kwargs
    ):
     #   if not settings.IGNORE_CREATION_FLOW:
     #       try:
     #           if is_update_request and self.extension_number.number != previous_number:
     #    #            KazooKamailioDatabase.unregister(
     #    #                previous_number,
     #    #                reload=False,
     #    #            )
     #                AsteriskDatabase.unregister(
     #                    extension=previous_number,
     #                    password=previous_password,
     #                )
     #           if self.has_pro:
     #    #            KazooKamailioDatabase.register(
     #    #                self.extension_number.number,
     #    #                self.password,
     #    #                self.prime_code,
     #    #            )
     #           else:
     #    #           KazooKamailioDatabase.unregister(
     #    #               self.extension_number.number,
     #    #           )
        AsteriskDatabase.register(
            extension=self.extension_number.number,
            password=self.password,
        )
     #       except Exception as e:
     #           logger.error("Exception: %s" % e)
     #           raise

        if settings.LI_ENABLED and self.subscription is not None:
            if self.__previous_status != ExtensionStatus.FORWARD.Value and  self.status == ExtensionStatus.FORWARD.Value:
                self.send_cfu_iri_report(
                    IRIConstants.SERVICE_ACTION.ACTIVATION,
                )

            elif self.__previous_status == ExtensionStatus.FORWARD.Value and self.status != ExtensionStatus.FORWARD.Value:
                self.send_cfu_iri_report(
                    IRIConstants.SERVICE_ACTION.DEACTIVATION,
                )

            if not self.__previous_call_waiting and self.call_waiting:
                self.send_cw_iri_report(IRIConstants.SERVICE_ACTION.ACTIVATION)

            elif self.__previous_call_waiting and not self.call_waiting:
                self.send_cw_iri_report(
                    IRIConstants.SERVICE_ACTION.DEACTIVATION)

        super(Extension, self).save(**kwargs)


@receiver(models.signals.post_delete, sender=Extension)
def delete_extension_signal_handler(sender, instance, **kwargs):
    if not settings.IGNORE_CREATION_FLOW:
        if instance.extension_number:
            try:
                KazooKamailioDatabase.unregister(
                    instance.extension_number.number,
                )
                AsteriskDatabase.unregister(
                    extension=instance.extension_number.number,
                    password=instance.password,
                )
                instance.extension_number.delete()
            except Exception as e:
                logger.error("Exception %s" % e)
