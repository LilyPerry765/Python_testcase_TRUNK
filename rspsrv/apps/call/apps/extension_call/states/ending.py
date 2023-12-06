import time

from rspsrv.apps.call.apps.base import SimpleState, EndingCause
from rspsrv.apps.call.apps.extension_call.states.base import (
    ExtensionCallStateName
)
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.call_pool import Calls
from rspsrv.apps.subscription.utils import normalize_outbound_number


class EndingState(SimpleState):
    state_name = ExtensionCallStateName.ENDING

    def __init__(self, machine, **kwargs):
        super(EndingState, self).__init__(machine=machine, **kwargs)
        self.events.recording = None
        self.cause = None
        self.talk_time = None

    def enter(self, cause=None):
        self.cause = cause
        self.machine.ending_time = time.time()
        self.talk_time = self.machine.get_talk_time()
        self.machine.blinded = True

        if (
                cause != EndingCause.CALLEE_ATRANSFERRED and
                cause != EndingCause.CALLER_ATRANSFERRED
        ):
            if cause == EndingCause.CALLEE_TRANSFERRED:
                self.machine.channel.hangup()
            elif cause == EndingCause.CALLER_TRANSFERRED:
                if self.machine.callee_channel:
                    self.machine.callee_channel.hangup()
            elif hasattr(self.machine, "callee_channel"):
                if (
                        self.machine.conferenced or
                        self.machine.channel.conferenced_channel is None
                ):
                    if self.machine.callee_channel:
                        self.machine.callee_channel.hangup()

        if (
                cause == EndingCause.CALLER_HANGUP or
                cause == EndingCause.CALLER_DESTROYED
        ):
            self.handlers.bridge.protected = False

        print("Next: ", self.machine.next)
        print("Machine history: ", ", ".join(map(lambda t: "%s-> %s" % (
            str(t[0]),
            str(t[1])
        ), self.machine.history)))
        self.cleanup()

        if self.machine.counted_ongoing_call:
            Calls.remove_call(
                self.machine.subscription.number,
                self.machine.channel.ongoing_call
            )

        previous_state = self.machine.history[-2][1]
        if not (
                cause == EndingCause.CALLER_TRANSFERRED and
                previous_state == self.machine.app_states.setup
        ):
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.END,
                affected_number=normalize_outbound_number(
                    self.machine.channel.source_number
                ),
                end_cause=cause
            )

        end_cause = (
            EndingCause.CALLER_TRANSFERRED,
            EndingCause.CALLER_CONFERENCING_CANCELED,
            EndingCause.CALLER_ATRANSFERRING_CANCELED,
            EndingCause.CALLER_ATRANSFERRED,
            EndingCause.CALLEE_CONFERENCED,
            EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
        )

        if (
                cause not in end_cause and
                not self.machine.channel.conferenced_channel
        ):
            if self.machine.channel:
                self.machine.channel.hangup()

        # we own (created) the bridge or we own shit?
        self.machine.end(
            cause=cause,
            next=self.machine.next,
            cdr_action=self.machine.cdr_action,
            endpoint_type=self.machine.endpoint_type,
            endpoint_name=self.machine.endpoint_name
        )

    def __str__(self):
        return EndingState.state_name
