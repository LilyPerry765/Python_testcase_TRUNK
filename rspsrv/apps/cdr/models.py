import datetime
import logging
import time

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

from rspsrv.apps.call.apps.base import EndingCause, CDRAction
from rspsrv.apps.call.call_control.types import CallType
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.utility import BaseChoice, RespinaBaseModel

logger = logging.getLogger("common")

CALL_TYPE_CHOICES = (
    (0, CallType.SMS),
    (1, CallType.VOICE),
    (2, 'Chat'),
    (3, CallType.FAX),
    (4, 'Voice Mail'),
    (5, CallType.VIDEO)
)

GET_CALL_TYPE_INT = {
    CallType.SMS: 0,
    CallType.VOICE: 1,
    'Chat': 2,
    CallType.FAX: 3,
    'Voice Mail': 4,
    CallType.VIDEO: 5
}

ACTION_CHOICES = (
    (CDRAction.TRANSFERRED, 'Transferred'),
    (CDRAction.CONFERENCED, 'Conferenced')
)

DIRECTION_CHOICES = (
    ('incoming', 'Incoming'),
    ('outgoing', 'Outgoing'),
    ('internal', 'Internal'),
)
DIRECTION_CONTEXT = (
    ('inbound', 'Inbound'),
    ('outbound', 'Outbound'),
)


class CDRState(object):
    Open = BaseChoice(label='Open', value='open')
    Closed = BaseChoice(label='Closed', value='closed')


class CallerEndpointType(object):
    SipPhone = BaseChoice(label='Sip Phone', value='SIPPhone')
    App = BaseChoice(label='App', value='APP')
    WebRTC = BaseChoice(label='WebRTC', value='WS')


CDR_STATE_CHOICES = (
    (CDRState.Open.Value, CDRState.Open.Label),
    (CDRState.Closed.Value, CDRState.Closed.Label),
)

CALLER_ENDPOINT_TYPE_CHOICES = (
    (CallerEndpointType.SipPhone.Value, CallerEndpointType.SipPhone.Label),
    (CallerEndpointType.App.Value, CallerEndpointType.App.Label),
    (CallerEndpointType.WebRTC.Value, CallerEndpointType.WebRTC.Label)
)

fs_extension_recorded_audio = FileSystemStorage(
    location=settings.APPS['recorded_call'])


def get_cdr_recorded_audio_location(instance, filename):
    return "cdr/{call_id}/{file_name}".format(call_id=instance.call_id,
                                              file_name=filename.replace(' ',
                                                                         '_'))


def get_time_now():
    return datetime.datetime.now().time()


def get_caller_callee_info(caller, callee, direction):
    caller_subscription, caller_customer, \
    callee_subscription, callee_customer = None, None, None, None
    if direction == DIRECTION_CONTEXT[0][0]:
        try:
            callee = Subscription.objects.get(
                number=callee,
                is_allocated=True,
            )
            callee_subscription = callee.subscription_code
            callee_customer = callee.customer.id
        except Subscription.DoesNotExist:
            pass
    if direction == DIRECTION_CONTEXT[1][0]:
        try:
            caller = Subscription.objects.get(
                number=caller,
                is_allocated=True,
            )
            caller_subscription = caller.subscription_code
            caller_customer = caller.customer.id
        except Subscription.DoesNotExist:
            pass

    return caller_customer, callee_customer, \
           caller_subscription, callee_subscription,


class CDR(RespinaBaseModel):
    # It's Switch ID actually.
    call_id_prefix = models.IntegerField(
        db_index=True,
        default=settings.CALL_ID_PREFIX,
        null=True,
    )
    call_id = models.IntegerField(db_index=True)
    call_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    call_odate = models.DateField(
        default=timezone.now,
        db_index=True,
    )
    call_otime = models.TimeField(
        default=get_time_now,
        db_index=True,
    )
    caller = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
    )
    called = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_index=True,
    )
    caller_customer_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    callee_customer_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    caller_subscription_code = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    callee_subscription_code = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        db_index=True,
    )
    mask_number = models.CharField(max_length=255, blank=True, null=True)
    caller_extension = models.CharField(max_length=32, blank=True, null=True)
    called_extension = models.CharField(max_length=32, blank=True, null=True)
    parent_extension_number = models.CharField(
        max_length=32,
        blank=True,
        null=True,
    )
    caller_trunk = models.CharField(max_length=128, blank=True)
    called_trunk = models.CharField(max_length=128, blank=True)
    duration = models.PositiveIntegerField(
        default=0,
        blank=True,
        db_index=True,
    )
    talk_time = models.PositiveIntegerField(
        default=0,
        blank=True,
        db_index=True,
    )
    rate = models.PositiveIntegerField(default=0)
    call_type = models.IntegerField(
        choices=CALL_TYPE_CHOICES,
        db_index=True,
    )
    call_state = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
    )
    action = models.CharField(
        max_length=32,
        choices=ACTION_CHOICES,
        blank=True,
    )
    action_value = models.CharField(max_length=32, blank=True)
    direction = models.CharField(max_length=32, blank=True)
    source_ip = models.CharField(max_length=64, blank=True)
    destination_ip = models.CharField(max_length=64, blank=True)
    caller_name = models.CharField(max_length=128, blank=True)
    called_name = models.CharField(max_length=128, blank=True)
    caller_extension_endpoint_type = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        choices=CALLER_ENDPOINT_TYPE_CHOICES,
    )
    caller_extension_endpoint_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    device_serial_number = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    reserved1 = models.CharField(max_length=128, null=True, blank=True)
    reserved2 = models.CharField(max_length=128, null=True, blank=True)
    end_cause = models.CharField(max_length=256, blank=True)
    state = models.CharField(
        max_length=8,
        choices=CDR_STATE_CHOICES,
        db_index=True,
    )
    recorded_audio = models.FileField(
        storage=fs_extension_recorded_audio,
        upload_to=get_cdr_recorded_audio_location,
        blank=True,
    )
    created_at = models.DateTimeField(
        default=datetime.datetime.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
    )

    class Meta:
        app_label = u'cdr'
        index_together = [
            [
                "talk_time",
                "call_odate",
                "call_otime",
                "caller",
                "called",
                "caller_extension",
                "called_extension",
                "created_at",
                "state",
            ],
        ]

    def __str__(self):
        caller = "unknown"
        called = "unknown"
        if self.caller:
            caller = self.caller
        elif self.caller_extension:
            caller = self.caller_extension

        if self.called:
            called = self.called
        elif self.called_extension:
            called = self.called_extension

        return " - ".join(
            [str(self.call_id), self.call_date.strftime("%y-%m-%d %H:%M:%S"),
             caller, called])

    @staticmethod
    def init_call_record(channel, call_id, **kwargs):
        cdr = CDR(
            call_id=call_id,
            caller=channel.endpoint_number,
            called=channel.destination_number,
            call_type=1,
            direction=channel.context,
        )

        for field_name in kwargs:
            try:
                cdr._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            setattr(cdr, field_name, kwargs.get(field_name))

        cdr.caller_customer_id, cdr.callee_customer_id, \
        cdr.caller_subscription_code, cdr.callee_subscription_code = \
            get_caller_callee_info(
                cdr.caller,
                cdr.called,
                cdr.direction,
            )

        cdr.state = 'open'
        cdr.save()
        return cdr

    @staticmethod
    def init_internal_record(channel, call_id, **kwargs):
        cdr = CDR(
            call_id=call_id,
            caller_extension=channel.endpoint_number,
            called_extension=channel.destination_number,
            call_type=1,
            direction=channel.context,
        )

        for field_name in kwargs:
            try:
                cdr._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            setattr(cdr, field_name, kwargs.get(field_name))

        cdr.state = 'open'
        cdr.save()
        return cdr

    @staticmethod
    def init_feature_call(channel, call_id, **kwargs):
        cdr = CDR(
            call_id=call_id,
            caller_extension=channel.endpoint_number,
            called=channel.destination_number,
            call_type=1,
            direction=channel.context,
        )

        for field_name in kwargs:
            try:
                cdr._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            setattr(cdr, field_name, kwargs.get(field_name))

        cdr.state = 'open'
        cdr.save()
        return cdr

    def close_record(self, **kwargs):
        if self.state == 'closed':
            return

        duration = kwargs.pop('duration', None)
        recorded_audio = kwargs.pop('recorded_audio', None)
        agent = kwargs.pop('agent', None)
        parent = kwargs.pop('parent', None)
        cdr_action = kwargs.pop('cdr_action', None)

        if duration:
            self.duration = int(duration)
        else:
            self.duration = int(
                time.time() - datetime.datetime.timestamp(self.created_at))

        if recorded_audio:
            self.recorded_audio.name = recorded_audio

        if agent:
            if parent:
                self.parent_extension_number = parent
                self.called_extension = agent
            else:
                self.parent_extension_number = self.called_extension
                self.called_extension = agent

        if cdr_action:
            self.action = cdr_action

        for field_name in kwargs:
            try:
                self._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            setattr(self, field_name, kwargs.get(field_name))

        self.state = 'closed'
        try:
            self.save()
        except:
            raise
        return self

    def set_extensions(self, caller_extension=None, called_extension=None):
        if caller_extension:
            self.caller_extension = caller_extension
        if called_extension:
            self.called_extension = called_extension

        try:
            self.save()
        except Exception as e:
            logger.error(e)

    def set_parent(self, parent_extension_number):
        self.parent_extension_number = parent_extension_number
        self.save()

    def call_renewed(self, new_extension_number):
        if self.called_extension:
            self.parent_extension_number = self.called_extension
        self.called_extension = new_extension_number

        try:
            self.save()
        except Exception as e:
            logger.error(e)

    @property
    def is_transfer(self):
        return self.end_cause in [EndingCause.CALLEE_ATRANSFERRED,
                                  EndingCause.CALLEE_TRANSFERRED,
                                  EndingCause.CALLER_TRANSFERRED,
                                  EndingCause.CALLER_ATRANSFERRED]
