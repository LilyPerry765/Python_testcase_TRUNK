import time

from rspsrv.apps.call.apps.base import GET_ENDING_CAUSE
from rspsrv.apps.call.apps.base import SimpleState, EndingCause, SimpleEvent
from rspsrv.apps.call.apps.defaults.ivr import ExternalPlayback
from rspsrv.apps.call.apps.external_call.states.base import (
    ExternalCallStateName,
)
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.call_pool import Calls
from rspsrv.apps.subscription.utils import normalize_outbound_number


class EndingState(SimpleState):
    state_name = ExternalCallStateName.ENDING

    def __init__(self, machine, **kwargs):
        super(EndingState, self).__init__(machine=machine, **kwargs)
        self.events.recording = None
        self.cause = None

        # Received Cause-Code (Reason-Code which Is Familiar for Asterisk).
        self.ending_reason_code = GET_ENDING_CAUSE[19]

    def playback_finished(self, **kwargs):
        self.machine.ending_time = time.time()

        if self.cause != EndingCause.CALLEE_ATRANSFERRED:
            if self.cause == EndingCause.CALLEE_TRANSFERRED:
                self.machine.channel.hangup(
                    reason=GET_ENDING_CAUSE[self.ending_reason_code],
                )
            elif hasattr(self.machine, 'callee_channel'):
                if (
                        self.machine.conferenced or
                        self.machine.channel.conferenced_channel is None
                ):
                    if self.machine.callee_channel:
                        if self.cause == EndingCause.CALLEE_HANGUP:
                            self.machine.callee_channel.hangup(
                                reason=GET_ENDING_CAUSE[self.ending_reason_code],
                            )
                        else:
                            self.machine.callee_channel.hangup()

        print("Next: ", self.machine.next)
        print(
            "Machine history: ", ", ".join(
                map(
                    lambda t: "%s-> %s" % (
                        str(t[0]),
                        str(t[1])
                    ),
                    self.machine.history
                )
            )
        )

        if self.machine.counted_ongoing_call:
            Calls.remove_call(
                self.machine.subscription.number,
                self.machine.channel.ongoing_call
            )

        if self.machine.conferenced:
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.END,
                affected_number=normalize_outbound_number(
                    self.machine.callee_channel.destination_number
                ),
                end_cause=self.cause,
                all_legs=True
            )

        if self.machine.forwarder_number:
            self.machine.channel.re_active_iris()
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.END,
                end_cause=self.cause,
                two_legs_only=True
            )

        else:
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.END,
                affected_number=normalize_outbound_number(
                                    self.machine.channel.destination_number),
                end_cause=self.cause
            )

        if (
                self.machine.callee_channel and
                not self.machine.callee_channel.is_transferred and
                not self.machine.channel.redirect_bridge
        ):
            # callee is not transferred nor conferenced, goodbye callee,
            # end billing
            self.machine.callee_channel.stop_billing()

        if self.machine.forwarder_number:
            # it was a outbound, transferred call
            self.machine.channel.stop_billing()

        if (
                self.machine.conferenced and
                self.machine.channel.conferenced_channel
        ):
            # it is a conferenced call
            self.machine.channel.conferenced_channel.stop_billing()

        if (
                self.machine.callee_channel and
                self.machine.callee_channel.is_transferred
        ):
            self.machine.channel.move_spy_iris(self.machine.callee_channel)

        if (
                self.cause not in (
                    EndingCause.CALLER_TRANSFERRED,
                    EndingCause.CALLER_CONFERENCING_CANCELED,
                    EndingCause.CALLER_ATRANSFERRING_CANCELED,
                    EndingCause.CALLER_ATRANSFERRED,
                    EndingCause.CALLEE_CONFERENCED,
                    EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
                ) and
                not self.machine.channel.conferenced_channel
        ):
            if self.machine.channel:
                if 'reason' in kwargs:
                    self.machine.channel.hangup(
                        reason=GET_ENDING_CAUSE[kwargs.get('reason')]
                    )
                else:
                    self.machine.channel.hangup(
                        reason=GET_ENDING_CAUSE[self.ending_reason_code],
                    )

        self.machine.channel.redirect_bridge = None
        self.cleanup()
        self.machine.end(
            cause=self.cause,
            next=self.machine.next,
            cdr_action=self.machine.cdr_action,
            endpoint_type=self.machine.endpoint_type,
            endpoint_name=self.machine.endpoint_name
        )

    def enter(self, cause=None, **kwargs):
        print("Cause: %s" % cause)
        valid_cause_codes = [16, 17, 19, 20, 31, 50]
        self.cause = cause
        query_params = {}

        cause_code = kwargs.get('cause_code', 0)
        if cause_code in valid_cause_codes:
            self.ending_reason_code = cause_code
            query_params['reason'] = cause_code
            ending_playback = ExternalPlayback.Ending.playback(
                self.machine.channel,
                cause_code,
                next=self.machine.next
            )
            ending_playback.on_event(
                SimpleEvent.Application.FINISHED,
                self.playback_finished
            )
            ending_playback.enter()
        else:
            self.playback_finished(**query_params)

    def __str__(self):
        return EndingState.state_name
