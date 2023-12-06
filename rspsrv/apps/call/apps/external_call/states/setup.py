from threading import Timer

from django.conf import settings

from rspsrv.apps.call.apps.base import SimpleEvent, EndingCause, SimpleState
from rspsrv.apps.call.apps.external_call.events import ExternalCallEvent
from rspsrv.apps.call.apps.external_call.states.base import (
    ExternalCallStateName
)
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.bridge import Bridge, BridgeType
from rspsrv.apps.call.call_control.call_pool import Calls, CallDirection
from rspsrv.apps.call.call_control.channel import (
    Channel,
    ChannelContext,
    ChannelIntent,
)
from rspsrv.apps.call.utils import timer_hangup
from rspsrv.apps.extension.models import ExtensionStatus
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.utils import (
    is_number_international,
    get_number,
    normalize_outbound_number,
)


class SetupState(SimpleState):
    state_name = ExternalCallStateName.SETUP

    def __init__(self, state_machine, **kwargs):
        super(SetupState, self).__init__(state_machine=state_machine, **kwargs)

    def __call_to(self, app_args='outbound', ring_back=True, caller_id=None):
        number = get_number(self.machine.target_number)
        try:
            Subscription.objects.get(number=number)
            is_local = True
        except Subscription.DoesNotExist:
            is_local = False

        self.machine.callee_channel = Channel.create_channel(
            self.machine.target_number,
            app_args,
            originator=self.machine.channel,
            channel_context=ChannelContext.OUTBOUND,
            endpoint_context="@LB",
            caller_id=caller_id,
            is_local=is_local,
            forwarded=self.machine.forwarder_number,
            timeout=self.machine.ring_max_seconds,
            billing_control=self.machine.billing_control
        )

        if self.machine.callee_channel is None:
            return None

        if ring_back:
            self.machine.channel.raw_channel.ring()

        self.events.callee_created = \
            self.machine.callee_channel.raw_channel.on_event(
                SimpleEvent.Channel.STATE_CHANGE,
                self.on_callee_channel_created
            )
        self.events.callee_destroyed = \
            self.machine.callee_channel.raw_channel.on_event(
                SimpleEvent.Channel.DESTROYED,
                self.on_callee_channel_destroyed
            )

        self.set_affected_channel_iri(self.machine.callee_channel)
        self.set_affected_channel_icc(self.machine.callee_channel)

        if self.machine.billing_control:
            self.machine.billing_control.set_channel(self.machine.callee_channel.uid)
            self.machine.billing_control = None

        if self.machine.channel.is_endpoint_internal():
            if self.machine.channel.intent == ChannelIntent.CALL:
                Calls.set_call(
                    self.machine.subscription.number,
                    CallDirection.OUTBOUND
                )
                self.machine.counted_ongoing_call = True
                self.machine.channel.ongoing_call = CallDirection.OUTBOUND
            elif (
                    self.machine.channel.intent == ChannelIntent.CONFERENCE and
                    self.machine.channel.ongoing_call is None
            ):
                Calls.set_call(
                    self.machine.subscription.number,
                    CallDirection.OUTBOUND
                )
                self.machine.counted_ongoing_call = True
                self.machine.channel.ongoing_call = CallDirection.OUTBOUND

        return self.machine.callee_channel

    def on_callee_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.DESTROYED, cause=EndingCause.CALLEE_DESTROYED,
                                  cause_code=event['cause'])

    def on_callee_channel_created(self, raw_channel, event):
        if event['channel']['state'] == SimpleEvent.Channel.RINGING:
            print(event)
            print("Callee channel created.")
            self.cleanup()
            self.machine.change_state(ExternalCallEvent.Callee.CREATED)
        elif event['channel']['state'] == SimpleEvent.Channel.UP:
            print(event)
            print("Callee channel created.")
            self.machine.channel.raw_channel.answer()
            Timer(
                settings.MAX_CALL_DURATION_SECONDS,
                timer_hangup,
                [self.machine.channel.raw_channel],
            ).start()
            self.cleanup()
            self.machine.change_state(SimpleEvent.Channel.TALKING_STARTED)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.next = None
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(ExternalCallEvent.Caller.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.next = None
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(ExternalCallEvent.Caller.HANGUP, cause=EndingCause.CALLER_HANGUP)

    @staticmethod
    def get_cause(status):
        cause = {
            ExtensionStatus.DISABLE: EndingCause.CALLEE_DISABLED,
            ExtensionStatus.DND: EndingCause.CALLEE_DND,
            ExtensionStatus.OFFLINE: EndingCause.CALLEE_NAVAILABLE
        }

        return cause.get(status, None)

    # set affected channel as self.machine.callee_channel in self.machine.channel iris
    def set_affected_channel_iri(self, channel):
        for iri in self.machine.channel.spy_iris:
            if not iri.affected_channel:
                iri.affected_channel = channel
        return

    def set_affected_channel_icc(self, channel):
        for icc in self.machine.channel.spy_iccs:
            if not icc.affected_channel:
                icc.affected_channel = channel
        return

    def enter(self):
        if self.machine.forwarder_number:
            self.machine.channel.set_forwarded_to_party(
                self.machine.channel.destination_number
            )

            if self.machine.channel.is_transferred:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    supps_type={
                        'service_action': IRIConstants.SERVICE_ACTION.ACTIVATION,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.ECT,
                        'party_number': self.machine.forwarder_number,
                    },
                )
            else:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    supps_type={
                        'service_action': IRIConstants.SERVICE_ACTION.ACTIVATION,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.CFU,
                        'party_number': self.machine.channel.source_number,
                        },
                        )

        elif self.machine.channel.redirect_bridge:
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.BEGIN,
                affected_number=normalize_outbound_number(
                    self.machine.channel.destination_number
                ),
                supps_type={
                    'service_action': IRIConstants.SERVICE_ACTION.ESTABLISHED,
                    'type': IRIConstants.SUPPLEMENTARY_SERVICE.CNF,
                    'party_number': self.machine.channel.destination_number,
                },
            )

        else:
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.BEGIN,
                affected_number=normalize_outbound_number(
                    self.machine.channel.destination_number
                )
            )

        if (
                self.machine.channel.intent == ChannelIntent.CALL and
                self.machine.subscription
        ):
            calls = Calls.get_calls_by_number(
                self.machine.subscription.number
            )

            if calls >= self.machine.subscription.max_call_concurrency:
                self.cleanup()
                self.machine.change_state(
                    SimpleEvent.Call.MAX_CONCURRENCY,
                    cause=EndingCause.MAX_CALL_CONCURRENCY
                )

        if self.machine.caller_extension.external_call_enable is False:
            self.cleanup()
            self.machine.change_state(
                SimpleEvent.Call.RESTRICTED,
                cause=EndingCause.CALL_RESTRICTED
            )

            return

        if (
                is_number_international(self.machine.target_number) and
                not self.machine.caller_extension.international_call
        ):
            self.cleanup()
            self.machine.change_state(
                SimpleEvent.Call.RESTRICTED,
                cause=EndingCause.CALL_RESTRICTED
            )

            return

        self.events.channel_destroyed = \
            self.machine.channel.raw_channel.on_event(
                SimpleEvent.Channel.DESTROYED,
                self.on_channel_destroyed
            )

        self.events.channel_hangup = self.machine.channel.raw_channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_channel_hangup
        )

        self.handlers.bridge = Bridge.create_bridge(BridgeType.MIXING)

        if self.__call_to(
                ring_back=self.machine.ring_back,
                caller_id=self.machine.caller_id
        ) is None:
            self.cleanup()
            self.machine.change_state(
                ExternalCallEvent.Callee.DESTROYED,
                cause=EndingCause.CALLEE_NAVAILABLE
            )

    def __str__(self):
        return SetupState.state_name
