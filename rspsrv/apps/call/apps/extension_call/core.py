import logging
import math
import os
import time

from requests.exceptions import HTTPError

from rspsrv.apps.call.apps.base import (
    SimpleEvent, BaseCallApplication,
    CallApplicationType,
)
from rspsrv.apps.call.apps.extension_call.events import ExtensionEvent
from rspsrv.apps.call.apps.extension_call.states.conferencing import (
    ConferencingState,
)
from rspsrv.apps.call.apps.extension_call.states.connected import (
    ConnectedState,
)
from rspsrv.apps.call.apps.extension_call.states.ending import EndingState
from rspsrv.apps.call.apps.extension_call.states.ringing import RingingState
from rspsrv.apps.call.apps.extension_call.states.setup import SetupState
from rspsrv.apps.call.apps.extension_call.states.transferring import (
    TransferringState,
)
from rspsrv.apps.call.call_control.channel import ChannelContext
from rspsrv.apps.extension.models import Extension

logger = logging.getLogger("call")


class ExtensionCall(BaseCallApplication):
    app_name = "Extension Call"
    app_detail = "Handles internal driven call."
    DefaultHoldingBridge = None

    def __init__(self, caller_channel, target_number, ring_back=True, timeout=None, attach_inbox=True, bridge=None,
                 call_id=None, **kwargs):
        super(ExtensionCall, self).__init__(channel=caller_channel, target_number=target_number)

        self.counted_ongoing_call = False
        self.blinded = False
        self.recorded_audio_name = None
        self.recorder_channel = None

        self.cdr = kwargs.get('cdr')

        try:
            self.extension_webapp = Extension.objects.get(extension_number__number=target_number)
        except (Extension.DoesNotExist, Extension.MultipleObjectsReturned) as e:
            raise BaseCallApplication.WebAppNotExists(e)

        if not self.extension_webapp.enabled:
            raise BaseCallApplication.WebAppRestriction("Extension is not enabled.")

        if self.extension_webapp.inbox_enabled:
            try:
                self.extension_webapp.inbox
            except Exception as e:
                raise BaseCallApplication.WebAppNotExists(e)

        self.subscription = kwargs.get('subscription', None)

        self.call_id = call_id

        self.next = None
        if self.extension_webapp.inbox_enabled and attach_inbox:
            self.next = (CallApplicationType.INBOX, target_number)

        self.cdr_action = None

        self.caller_extension = None

        self.callee_channel = None

        self.ring_back = ring_back

        self.handlers.bridge = bridge

        self.endpoint_type = None
        self.endpoint_name = None

        self.forwarder_number = None
        if 'forwarder_extension' in kwargs and kwargs['forwarder_extension']:
            self.forwarder_number = kwargs.get('forwarder_extension').number

        self.forwarder_app = kwargs.pop('forwarder_app', None)

        if timeout is not None:
            self.ring_max_seconds = timeout
        else:
            self.ring_max_seconds = self.extension_webapp.ring_seconds

        self.ringing_time = None
        self.talking_time = None
        self.ending_time = None
        self.external_ending_cause = None

        self.conferenced = False

        if caller_channel.context == ChannelContext.INTERNAL:
            print("Caller channel number:", caller_channel.endpoint_number)

            if 'forwarder_extension' in kwargs:
                try:
                    self.caller_extension = Extension.objects.get(
                        extension_number__number=kwargs.pop('forwarder_extension').number)
                except Exception:
                    pass
            if not self.caller_extension:
                try:
                    self.caller_extension = Extension.objects.get(
                        extension_number__number=caller_channel.endpoint_number)
                except (Extension.DoesNotExist, Extension.MultipleObjectsReturned) as e:
                    raise BaseCallApplication.WebAppNotExists(e)

        self.local_caller = False

        self.waiting_call = False

        self.record = True

        if self.caller_extension:
            if not self.caller_extension.record_all:
                self.record = False
        if not self.extension_webapp.record_all:
            self.record = False

        self.recording_path = os.path.join('cdr', call_id)

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

    def on_callee_channel_hold(self, *args):
        try:
            self.handlers.bridge.remove_channel(channel=self.callee_channel)
        except HTTPError as e:
            logger.error(e)
        if not self.conferenced:
            try:
                self.channel.raw_channel.startMoh()
            except HTTPError as e:
                logger.error(e)

    def on_callee_channel_unhold(self, *args):
        try:
            self.handlers.bridge.add_channel(channel=self.callee_channel)
        except HTTPError as e:
            logger.error(e)

        try:
            self.channel.raw_channel.stopMoh()
        except HTTPError as e:
            logger.error(e)

    def on_conferenced_channel_hold(self, *args):
        try:
            self.handlers.bridge.remove_channel(channel=self.channel.conferenced_channel)
        except HTTPError as e:
            logger.error(e)
        if not self.conferenced:
            try:
                self.channel.raw_channel.startMoh()
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

    def on_conferenced_channel_hangup(self, raw_channel, event):
        self.channel.conferenced_channel = None

    def on_conferenced_channel_destroyed(self, raw_channel, event):
        self.channel.conferenced_channel = None

    def __setup_state_machine(self):
        self.app_states.setup = SetupState(self)
        self.app_states.ringing = RingingState(self)
        self.app_states.connected = ConnectedState(self)
        self.app_states.ending = EndingState(self)
        self.app_states.transferring = TransferringState(self)
        self.app_states.conferencing = ConferencingState(self)

        self.initial_state = self.app_states.setup
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.setup, ExtensionEvent.Callee.CREATED, self.app_states.ringing)
        self.add_transition(self.app_states.setup, ExtensionEvent.Caller.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, ExtensionEvent.Callee.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, ExtensionEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.setup, ExtensionEvent.Caller.BTRANSFERRED, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Base.TIMELY_REJECTION, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Base.CALLER_RESTRICTED, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Base.CALLEE_BUSY, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Call.MAX_CONCURRENCY, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.TALKING_STARTED, self.app_states.connected)

        self.add_transition(self.app_states.ringing, SimpleEvent.Channel.TALKING_STARTED, self.app_states.connected)
        self.add_transition(self.app_states.ringing, ExtensionEvent.Callee.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExtensionEvent.Callee.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExtensionEvent.Caller.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExtensionEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.ringing, ExtensionEvent.Callee.NO_ANSWER, self.app_states.ending)
        self.add_transition(
            self.app_states.ringing,
            ExtensionEvent.Caller.CONFERENCING_CANCELED,
            self.app_states.ending
        )
        self.add_transition(
            self.app_states.ringing,
            ExtensionEvent.Caller.ATRANSFERRING_CANCELED,
            self.app_states.ending
        )

        self.add_transition(self.app_states.connected, ExtensionEvent.Callee.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Caller.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Callee.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Caller.BTRANSFERRED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Callee.BTRANSFERRED, self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Callee.ATRANSFERRING,
                            self.app_states.transferring)
        self.add_transition(self.app_states.connected, ExtensionEvent.Caller.ATRANSFERRING,
                            self.app_states.transferring)
        self.add_transition(self.app_states.connected, ExtensionEvent.Caller.CONFERENCING, self.app_states.conferencing)
        self.add_transition(self.app_states.connected, ExtensionEvent.Caller.CONFERENCING_CANCELED,
                            self.app_states.ending)
        self.add_transition(self.app_states.connected, ExtensionEvent.Callee.CONFERENCED,
                            self.app_states.ending)

        self.add_transition(self.app_states.transferring, ExtensionEvent.Callee.ATRANSFERRED, self.app_states.ending)
        self.add_transition(self.app_states.transferring, ExtensionEvent.Caller.ATRANSFERRED, self.app_states.ending)
        self.add_transition(self.app_states.transferring, ExtensionEvent.Callee.ATRANSFERRING_CANCELED,
                            self.app_states.connected)
        self.add_transition(self.app_states.transferring, ExtensionEvent.Caller.ATRANSFERRING_CANCELED,
                            self.app_states.connected)
        self.add_transition(self.app_states.connected, ExtensionEvent.Callee.ATRANSFERRING_NACCEPT,
                            self.app_states.ending)

        self.add_transition(self.app_states.conferencing, ExtensionEvent.Caller.CONFERENCED, self.app_states.connected)
        self.add_transition(self.app_states.conferencing, ExtensionEvent.Caller.CONFERENCING_CANCELED,
                            self.app_states.connected)
        self.add_transition(self.app_states.conferencing, ExtensionEvent.Caller.HANGUP, self.app_states.ending)
        self.add_transition(self.app_states.conferencing, ExtensionEvent.Caller.DESTROYED, self.app_states.ending)

    def enter(self):
        super(ExtensionCall, self).enter()
        self.__setup_state_machine()
        self.start()

    @classmethod
    def get_name(cls):
        return cls.app_name

    @classmethod
    def get_detail(cls):
        return cls.app_detail

    def get_talk_time(self):
        if self.talking_time and self.ending_time:
            print("Talk time:", float(self.ending_time - self.talking_time))
            return math.ceil(float(self.ending_time - self.talking_time))
        elif self.talking_time:
            return math.ceil(float(time.time() - self.talking_time))
        return 0

    def get_recorded_audio_name(self):
        if self.record:
            return self.recorded_audio_name

    def __str__(self):
        return ExtensionCall.app_name

    def terminate(self, **kwargs):
        print("Termination called for ", self.target_number)
        super(ExtensionCall, self).terminate(**kwargs)
