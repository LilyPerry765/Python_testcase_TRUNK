import re
import time

from django.conf import settings
from requests.exceptions import HTTPError

from rspsrv.apps.call.apps.base import (
    SimpleEvent,
    SimpleState,
    EndingCause,
    SimpleTimeout,
)
from rspsrv.apps.call.apps.external_call.events import ExternalCallEvent
from rspsrv.apps.call.apps.external_call.states.base import (
    ExternalCallStateName
)
from rspsrv.apps.call.call_control.channel import (
    ChannelIntent,
)
from rspsrv.apps.call.call_control.iri import IRIConstants
from rspsrv.apps.call.call_control.live_recording import LiveRecording
from rspsrv.apps.subscription.utils import normalize_outbound_number

pattern = re.compile("\*\d\*\d+#")


class CallCommand(object):
    BLIND_TRANSFER = "1"
    ATTENDED_TRANSFER = "2"
    CONFERENCING = "3"
    HOLDING = "4"
    MUTING = "5"


class ConnectedState(SimpleState):
    state_name = ExternalCallStateName.CONNECTED

    def __init__(self, state_machine, **kwargs):
        self.caller_dtmf_string = ''
        self.callee_dtmf_string = ''
        self.conference_target = None

        self.redirected = False
        super(ConnectedState, self).__init__(
            state_machine=state_machine,
            **kwargs,
        )

    def on_callee_destroyed(self, raw_channel, event):
        print("CALLEE DESTROYED")
        if self.machine.channel.conferenced_channel is not None:
            self.machine.callee_channel.stop_billing()
            self.machine.callee_channel.billing_control = None
            return

        if self.machine.channel.conferenced_channel is not None:
            return

        self.cleanup()
        self.machine.change_state(
            ExternalCallEvent.Callee.DESTROYED,
            cause=EndingCause.CALLEE_DESTROYED,
        )

    def on_callee_hungup(self, raw_channel, event):
        print("CALLEE HUNGUP")
        if self.machine.channel.conferenced_channel is not None:
            self.machine.callee_channel.stop_billing()
            self.machine.callee_channel.billing_control = None
            return

        if self.machine.channel.conferenced_channel is not None:
            return

        self.cleanup()
        self.machine.change_state(
            ExternalCallEvent.Callee.HANGUP,
            cause=EndingCause.CALLEE_HANGUP,
        )

    def on_caller_destroyed(self, raw_channel, event):
        print("CALLER DESTROYED")
        if self.machine.blinded:
            print("was blinded...")
            return
        if self.redirected:
            self.redirected = False
            return
        print("Redirect channel:", self.machine.channel.redirect_channel)
        if self.machine.channel.redirect_channel:
            print(self.machine.channel.redirect_channel.alive, "<--- ALIVE")
            if self.machine.channel.redirect_channel.alive and not self.redirected:
                self.events.caller_hungup.close()
                self.redirected = True
                self.machine.channel.redirect_channel.raw_channel.unhold()
                self.handlers.bridge.add_channel(
                    channel=self.machine.channel.redirect_channel,
                )
                self.change_caller_channel(
                    channel=self.machine.channel.redirect_channel,
                )
                return

        self.cleanup()

        try:
            self.handlers.bridge.add_channel(
                channel=self.machine.callee_channel,
            )
        except HTTPError:
            pass

        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(
            ExternalCallEvent.Caller.DESTROYED,
            cause=EndingCause.CALLER_DESTROYED,
        )

    def on_caller_hungup(self, raw_channel, event):
        print("CALLER HANGUP")
        if self.machine.blinded:
            print("was blinded...")
            return
        if self.redirected:
            self.redirected = False
            return
        print("Redirect channel:", self.machine.channel.redirect_channel)
        if self.machine.channel.redirect_channel:
            print(self.machine.channel.redirect_channel.alive, "<--- ALIVE")
            if self.machine.channel.redirect_channel.alive and not self.redirected:
                self.events.caller_hungup.close()
                self.redirected = True
                self.machine.channel.redirect_channel.raw_channel.unhold()
                self.handlers.bridge.add_channel(
                    channel=self.machine.channel.redirect_channel,
                )
                self.change_caller_channel(
                    channel=self.machine.channel.redirect_channel,
                )
                return

        self.cleanup()

        try:
            self.handlers.bridge.add_channel(
                channel=self.machine.callee_channel)
        except HTTPError:
            pass

        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(
            ExternalCallEvent.Caller.HANGUP,
            cause=EndingCause.CALLER_HANGUP,
        )

    def on_timeout(self, *args, **kwargs):
        self.cleanup()
        print(
            'External Call Timeout : {} to {}'.format(
                self.machine.caller_id,
                self.machine.channel.destination_number
            )
        )
        self.machine.change_state(SimpleEvent.Timeout.GLOBAL,
                                  cause=EndingCause.APP_TIMEOUT)

    def enter(self, **kwargs):
        if self.machine.cdr:
            self.machine.cdr.talk_time += 1
            self.machine.cdr.save()

        if self.machine.forwarder_number:
            if self.machine.channel.is_transferred:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.CONTINUE,
                    supps_type=
                    {
                        'service_action':
                            IRIConstants.SERVICE_ACTION.ACTIVATION,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.ECT,
                        'party_number': self.machine.forwarder_number,
                    },
                )
            else:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.CONTINUE,
                    supps_type=
                    {
                        'service_action':
                            IRIConstants.SERVICE_ACTION.ACTIVATION,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.CFU,
                        'party_number': self.machine.channel.source_number,
                    },
                )

        elif self.machine.channel.conferenced_channel is None:
            if self.machine.channel.redirect_bridge:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.CONTINUE,
                    supps_type={
                        'service_action': IRIConstants.SERVICE_ACTION.FLOATING,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.CNF,
                        'party_number':
                            self.machine.callee_channel.destination_number,
                    },
                    affected_number=normalize_outbound_number(
                        self.machine.callee_channel.destination_number
                    ),
                )

            else:
                self.machine.channel.send_packet(
                    IRIConstants.Record.CONTINUE,
                    affected_number=normalize_outbound_number(
                            self.machine.callee_channel.destination_number)
                )

        if (
                self.machine.channel.intent == ChannelIntent.CONFERENCE and
                self.machine.channel.conferenced_channel is None
        ):
            self.machine.channel.conferenced_channel = \
                self.machine.callee_channel

        self.machine.channel.is_transferred = False
        self.machine.next = None

        self.handlers.bridge.add_channel(channel=self.machine.channel)
        self.handlers.bridge.add_channel(channel=self.machine.callee_channel)

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

        self.events.timeout = SimpleTimeout(
            settings.EXTERNAL_CALL_TIMEOUT,
            self.on_timeout
        )

    def change_caller_channel(self, channel):
        self.machine.channel.move_spy_iccs(channel)
        self.machine.channel = channel

        self.events.caller_destroyed = self.machine.channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_caller_destroyed
        )

        self.events.caller_hungup = self.machine.channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_caller_hungup
        )

    def start_recording(self):
        self.machine.recorded_audio_name = ("%s_%s_%s" % (
            self.machine.channel.endpoint_number,
            self.machine.callee_extension,
            time.time())).replace('.', '_')

        self.machine.recorder_channel = self.machine.channel.get_spy(
            settings.SWITCHMANAGER_APP_NAME,
            spy='BOTH'.lower(),
            app_args="internal_snoop_in"
        )

        self.handlers.recording = LiveRecording.create_record_on_channel(
            self.machine.recorder_channel,
            path=self.machine.recording_path,
            name=self.machine.recorded_audio_name
        )

    def __str__(self):
        return ConnectedState.state_name
