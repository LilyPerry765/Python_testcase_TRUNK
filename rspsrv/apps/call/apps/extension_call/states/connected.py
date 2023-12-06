import logging
import re
import time

from django.conf import settings

from rspsrv.apps.call.apps.base import (
    SimpleEvent,
    SimpleState,
    EndingCause,
)
from rspsrv.apps.call.apps.extension_call.events import ExtensionEvent
from rspsrv.apps.call.apps.extension_call.states.base import (
    ExtensionCallStateName
)
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.channel import (
    ChannelIntent,
)
from rspsrv.apps.call.call_control.live_recording import LiveRecording
from rspsrv.apps.subscription.utils import normalize_outbound_number

logger = logging.getLogger("call")

pattern = re.compile("\*\d\*\d+#")


class CallCommand(object):
    BLIND_TRANSFER = "1"
    ATTENDED_TRANSFER = "2"
    CONFERENCING = "3"
    HOLDING = "4"
    MUTING = "5"


class ConnectedState(SimpleState):
    state_name = ExtensionCallStateName.CONNECTED

    def __init__(self, state_machine, **kwargs):
        super(ConnectedState, self).__init__(state_machine=state_machine, **kwargs)
        self.callee_dtmf_string = ""
        self.caller_dtmf_string = ""
        self.conference_target = ""
        self.redirected = False

    def on_callee_destroyed(self, raw_channel, event):
        print("CALLEE DESTROYED")
        if self.machine.blinded:
            return

        if self.machine.channel.conferenced_channel is not None:
            return

        if self.machine.channel.redirect_channel:
            cause = EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
        else:
            cause = EndingCause.CALLEE_DESTROYED
        self.cleanup()
        self.machine.next = None
        self.machine.change_state(ExtensionEvent.Callee.HANGUP, cause=cause)

    def on_callee_hungup(self, raw_channel, event):
        print("CALLEE HUNGUP")
        if self.machine.blinded:
            return

        if self.machine.channel.conferenced_channel is not None:
            return

        if self.machine.channel.redirect_channel:
            cause = EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
        else:
            cause = EndingCause.CALLEE_DESTROYED
        self.cleanup()
        self.machine.next = None
        self.machine.change_state(ExtensionEvent.Callee.HANGUP, cause=cause)

    def on_caller_destroyed(self, raw_channel, event):
        print('destroyed')
        if self.machine.blinded:
            return
        if self.redirected:
            self.redirected = False
            return
        if self.machine.channel.redirect_channel:
            if self.machine.channel.redirect_channel.alive and not self.redirected:
                self.events.caller_destroyed.close()
                self.redirected = True
                self.machine.channel.redirect_channel.raw_channel.unhold()
                self.handlers.bridge.add_channel(channel=self.machine.channel.redirect_channel)
                self.change_caller_channel(channel=self.machine.channel.redirect_channel)
                return
        print(self.machine.channel.endpoint_number, "CALLER DESTROYED")
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.cleanup()
        self.machine.change_state(ExtensionEvent.Caller.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_caller_hungup(self, raw_channel, event):
        print('hungup')
        if self.machine.blinded:
            print("was blinded...")
            return
        if self.redirected:
            self.redirected = False
            return
        if self.machine.channel.redirect_channel:
            if self.machine.channel.redirect_channel.alive and not self.redirected:
                self.events.caller_hungup.close()
                self.redirected = True
                self.machine.channel.redirect_channel.raw_channel.unhold()
                self.handlers.bridge.add_channel(channel=self.machine.channel.redirect_channel)
                self.change_caller_channel(channel=self.machine.channel.redirect_channel)
                return
        print(self.machine.channel.endpoint_number, "CALLER HANGUP")
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.cleanup()
        self.machine.change_state(ExtensionEvent.Caller.HANGUP, cause=EndingCause.CALLER_HANGUP)

    def enter(self, **kwargs):
        if self.machine.cdr:
            self.machine.cdr.talk_time += 1
            self.machine.cdr.save()

        if self.machine.waiting_call:
            self.machine.channel.send_packet(
                IRIConstants.Record.CONTINUE,
                affected_number=normalize_outbound_number(
                    self.machine.channel.source_number
                ),
                supps_type={
                    'service_action': IRIConstants.SERVICE_ACTION.ACTIVATION,
                    'type': IRIConstants.SUPPLEMENTARY_SERVICE.CW,
                    'party_number': self.machine.channel.destination_number,
                    }
                    )
        else:
            self.machine.channel.send_packet(
                IRIConstants.Record.CONTINUE,
                affected_number=normalize_outbound_number(
                self.machine.channel.source_number
                )
            )

        if (
                self.machine.channel.intent == ChannelIntent.CONFERENCE and
                self.machine.channel.conferenced_channel is None
            ):
            self.machine.channel.conferenced_channel = \
                self.machine.callee_channel

        self.machine.channel.is_transferred = False
        self.machine.final_state = "Answered"
        redirect_channel = kwargs.pop('redirect_channel', None)
        if redirect_channel is False:
            self.machine.channel.redirect_channel = None
            self.machine.callee_channel.redirect_channel = None

        self.machine.next = None

        try:
            self.handlers.bridge.add_channel(
                channel=self.machine.callee_channel
            )
            self.handlers.bridge.add_channel(channel=self.machine.channel)
        except Exception as error:
            logger.error(error)

        self.events.callee_destroyed = self.machine.callee_channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_callee_destroyed
        )

        self.events.callee_hungup = self.machine.callee_channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_callee_hungup
        )
        self.events.caller_destroyed = self.machine.channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_caller_destroyed
        )
        self.events.caller_hungup = self.machine.channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_caller_hungup
        )

        if self.machine.talking_time is None:
            self.machine.talking_time = time.time()

        if self.machine.recorder_channel is None:
            self.start_recording()

    def __str__(self):
        return ConnectedState.state_name

    def change_caller_channel(self, channel):
        self.machine.channel = channel
        self.events.caller_destroyed = self.machine.channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_caller_destroyed
        )

        self.events.caller_hungup = self.machine.channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_caller_hungup
        )

        if not self.machine.local_caller:
            self.handlers.channel_hold = self.machine.channel.on_event(
                SimpleEvent.Channel.HOLD,
                self.machine.on_caller_channel_hold
            )
            self.handlers.channel_unhold = self.machine.channel.on_event(
                SimpleEvent.Channel.UNHOLD,
                self.machine.on_caller_channel_unhold
            )

    def start_recording(self):
        self.machine.recorded_audio_name = ("%s_%s_%s" % (self.machine.channel.endpoint_number,
                                                          self.machine.callee_channel.endpoint_number,
                                                          time.time())).replace('.', '_')

        self.machine.recorder_channel = self.machine.callee_channel.get_spy(
            settings.SWITCHMANAGER_APP_NAME,
            spy='BOTH'.lower(),
            app_args="internal_snoop_in"
        )

        self.handlers.recording = LiveRecording.create_record_on_channel(
            self.machine.recorder_channel,
            path=self.machine.recording_path,
            name=self.machine.recorded_audio_name
        )
