import logging
import math
import os
import time

from requests.exceptions import HTTPError

from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent
from rspsrv.apps.call.apps.external_call.events import ExternalCallEvent
from rspsrv.apps.call.apps.external_call.states.conferencing import (
    ConferencingState,
)
from rspsrv.apps.call.apps.external_call.states.connected import ConnectedState
from rspsrv.apps.call.apps.external_call.states.ending import EndingState
from rspsrv.apps.call.apps.external_call.states.ringing import RingingState
from rspsrv.apps.call.apps.external_call.states.setup import SetupState
from rspsrv.apps.call.apps.external_call.states.transferring import (
    TransferringState,
)
from rspsrv.apps.extension.models import Extension
from rspsrv.apps.subscription.models import Subscription

logger = logging.getLogger("call")


class ExternalCall(BaseCallApplication):
    app_name = "External Call"
    app_detail = "Handles outbound calls."

    def __init__(self, caller_channel, target_number, ring_back=True, timeout=None, billing_control=None, **kwargs):
        super(ExternalCall, self).__init__(channel=caller_channel, target_number=target_number)

        self.counted_ongoing_call = False
        self.blinded = False
        self.next = None
        self.cdr_action = None

        self.cdr = kwargs.get('cdr')

        self.billing_control = billing_control

        self.recorded_audio_name = None

        self.callee_channel = None
        self.caller_extension = None
        self.callee_extension = target_number

        self.ring_back = ring_back

        self.blinded = False
        self.conferenced = False

        self.subscription = kwargs.get('subscription', None)
        self.call_id = kwargs.get('call_id', None)

        self.endpoint_type = None
        self.endpoint_name = None

        if timeout is not None:
            self.ring_max_seconds = timeout
        else:
            self.ring_max_seconds = 1800

        self.ringing_time = None
        self.talking_time = None
        self.ending_time = None

        if self.subscription is None:
            try:
                self.subscription = Subscription.objects.get_default(
                    caller_channel.endpoint_number,
                )
                self.caller_id = self.subscription.number
            except Subscription.DoesNotExist:
                self.caller_id = caller_channel.destination_number
        else:
            self.caller_id = self.subscription.number

        self.forwarder_number = None
        if 'forwarder_extension' in kwargs and kwargs['forwarder_extension']:
            self.forwarder_number = kwargs.get('forwarder_extension').number

            try:
                self.caller_extension = Extension.objects.get(
                    extension_number__number=kwargs.pop('forwarder_extension').number)
            except Exception:
                pass

        if not self.caller_extension:
            try:
                self.caller_extension = Extension.objects.get(extension_number__number=caller_channel.source_number)
            except (Extension.DoesNotExist, Extension.MultipleObjectsReturned):
                try:
                    self.caller_extension = Extension.objects.get(
                        extension_number__number=caller_channel.endpoint_number)
                except (Extension.DoesNotExist, Extension.MultipleObjectsReturned):
                    raise BaseCallApplication.WebAppNotExists

        self.record = True
        self.recorder_channel = None

        if self.caller_extension:
            if not self.caller_extension.record_all:
                self.record = False

        self.recording_path = os.path.join('cdr', self.call_id)

    def __setup_state_machine(self):
        self.app_states.setup = SetupState(self)
        self.app_states.ringing = RingingState(self)
        self.app_states.connected = ConnectedState(self)
        self.app_states.ending = EndingState(self)
        self.app_states.conferencing = ConferencingState(self)
        self.app_states.transferring = TransferringState(self)

        self.initial_state = self.app_states.setup
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.setup, ExternalCallEvent.Callee.CREATED, self.app_states.ringing)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.TALKING_STARTED, self.app_states.connected)
        self.add_transition(self.app_states.setup, SimpleEvent.Call.RESTRICTED, self.app_states.ending)
        self.add_transition(self.app_states.setup, ExternalCallEvent.Caller.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, ExternalCallEvent.Callee.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, ExternalCallEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Call.MAX_CONCURRENCY, self.app_states.ending)

        self.add_transition(self.app_states.ringing, SimpleEvent.Channel.TALKING_STARTED, self.app_states.connected)
        self.add_transition(self.app_states.ringing, ExternalCallEvent.Callee.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExternalCallEvent.Callee.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExternalCallEvent.Caller.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExternalCallEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExternalCallEvent.Callee.NO_ANSWER, self.app_states.ending)
        self.add_transition(
            self.app_states.ringing,
            ExternalCallEvent.Caller.CONFERENCING_CANCELED,
            self.app_states.ending
        )
        self.add_transition(
            self.app_states.ringing,
            ExternalCallEvent.Caller.ATRANSFERRING_CANCELED,
            self.app_states.ending
        )

        self.add_transition(self.app_states.connected, ExternalCallEvent.Callee.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExternalCallEvent.Caller.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExternalCallEvent.Callee.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExternalCallEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExternalCallEvent.Transfer.CANCELLED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExternalCallEvent.Conference.CANCELLED, self.app_states.ending)
        self.add_transition(
            self.app_states.connected,
            ExternalCallEvent.Caller.CONFERENCING,
            self.app_states.conferencing
        )
        self.add_transition(
            self.app_states.connected,
            ExternalCallEvent.Caller.CONFERENCING_CANCELED,
            self.app_states.ending
        )
        self.add_transition(
            self.app_states.connected,
            ExternalCallEvent.Caller.ATRANSFERRING,
            self.app_states.transferring
        )
        self.add_transition(
            self.app_states.connected,
            ExternalCallEvent.Callee.BTRANSFERRED,
            self.app_states.ending
        )
        self.add_transition(self.app_states.connected, ExternalCallEvent.Callee.CONFERENCED,
                            self.app_states.ending)
        self.add_transition(self.app_states.connected, ExternalCallEvent.Callee.ATRANSFERRING_NACCEPT,
                            self.app_states.ending)
        self.add_transition(self.app_states.connected, SimpleEvent.Timeout.GLOBAL,
                            self.app_states.ending)

        self.add_transition(
            self.app_states.conferencing,
            ExternalCallEvent.Caller.CONFERENCED,
            self.app_states.connected
        )
        self.add_transition(
            self.app_states.conferencing,
            ExternalCallEvent.Caller.CONFERENCING_CANCELED,
            self.app_states.connected
        )

        self.add_transition(
            self.app_states.transferring,
            ExternalCallEvent.Callee.ATRANSFERRED,
            self.app_states.ending
        )
        self.add_transition(
            self.app_states.transferring,
            ExternalCallEvent.Caller.ATRANSFERRING_CANCELED,
            self.app_states.connected
        )

    def enter(self):
        super(ExternalCall, self).enter()
        self.__setup_state_machine()
        self.start()

    def on_caller_channel_hold(self, *args):
        try:
            self.handlers.bridge.remove_channel(channel=self.callee_channel)
        except HTTPError as e:
            logger.error(e)

        try:
            self.callee_channel.raw_channel.startMoh()
        except HTTPError as e:
            logger.error(e)

        if self.channel.conferenced_channel:
            try:
                self.handlers.bridge.remove_channel(channel=self.channel.conferenced_channel)
            except HTTPError as e:
                logger.error(e)

            try:
                self.channel.conferenced_channel.raw_channel.startMoh()
            except HTTPError as e:
                logger.error(e)

    def on_caller_channel_unhold(self, *args):
        try:
            self.handlers.bridge.add_channel(channel=self.callee_channel)
        except HTTPError as e:
            logger.error(e)

        try:
            self.callee_channel.raw_channel.stopMoh()
        except HTTPError as e:
            logger.error(e)

        if self.channel.conferenced_channel:
            try:
                self.handlers.bridge.add_channel(channel=self.channel.conferenced_channel)
            except HTTPError as e:
                logger.error(e)

            try:
                self.channel.conferenced_channel.raw_channel.stopMoh()
            except HTTPError as e:
                logger.error(e)

    def on_conferenced_channel_hold(self, *args):
        try:
            self.handlers.bridge.remove_channel(channel=self.channel.conferenced_channel)
        except HTTPError as e:
            logger.error(e)

    def on_conferenced_channel_unhold(self, *args):
        try:
            self.handlers.bridge.add_channel(channel=self.channel.conferenced_channel)
        except HTTPError as e:
            logger.error(e)

        try:
            self.channel.raw_channel.stopMoh()
        except HTTPError as e:
            logger.error(e)

    def on_conferenced_channel_destroyed(self, raw_channel, event):
        print("CONFERENCED_TO PARTY DESTROYED")
        if self.channel.conferenced_channel:
            self.channel.conferenced_channel.stop_billing()
            self.channel.conferenced_channel = None

        self.channel.conferenced_channel = None

    def on_conferenced_channel_hungup(self, raw_channel, event):
        print("CONFERENCED_TO PARTY HUNGUP")
        if self.channel.conferenced_channel:
            self.channel.conferenced_channel.stop_billing()
            self.channel.conferenced_channel = None

        self.channel.conferenced_channel = None

    @classmethod
    def get_name(cls):
        return cls.app_name

    @classmethod
    def get_detail(cls):
        return cls.app_detail

    def get_talk_time(self):
        if self.talking_time and self.ending_time:
            return math.ceil(float(self.ending_time - self.talking_time))
        elif self.talking_time:
            return math.ceil(float(time.time() - self.talking_time))
        return 0

    def get_recorded_audio_name(self):
        if self.record:
            return self.recorded_audio_name

    def __str__(self):
        return ExternalCall.app_name

    def terminate(self, **kwargs):
        print("Termination called for ", self.target_number)
        super(ExternalCall, self).terminate(**kwargs)
