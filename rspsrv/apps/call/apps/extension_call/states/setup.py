import logging

from django.conf import settings
from requests import HTTPError

from rspsrv.apps.call.apps.base import (
    SimpleEvent, EndingCause, SimpleState,
    CallApplicationType,
)
from rspsrv.apps.call.apps.extension_call.events import ExtensionEvent
from rspsrv.apps.call.apps.extension_call.states.base import (
    ExtensionCallStateName
)
from rspsrv.apps.call.apps.playback.core import Playback
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.bridge import Bridge, BridgeType
from rspsrv.apps.call.call_control.call_pool import Calls, CallDirection
from rspsrv.apps.call.call_control.channel import (
    Channel,
    ChannelContext,
    ChannelIntent,
)
from rspsrv.apps.extension.models import ExtensionStatus, Extension
from rspsrv.apps.subscription.utils import normalize_outbound_number

logger = logging.getLogger("call")


class SetupState(SimpleState):
    state_name = ExtensionCallStateName.SETUP

    def __init__(self, state_machine, **kwargs):
        super(SetupState, self).__init__(state_machine=state_machine, **kwargs)
        self.caller = ""

    def __call_to(self, app_args='outgoing', ring_back=True, caller_id=None):
        sip_header = None
        if self.machine.channel.context == ChannelContext.INBOUND:
            sip_header = {
                'header_name': 'GatewayNumber',
                'header_value': self.machine.channel.destination_number
            }

        self.machine.callee_channel = Channel.create_channel(
            self.machine.target_number,
            app_args,
            originator=self.machine.channel,
            channel_context=ChannelContext.INTERNAL,
            endpoint_context='',
            caller_id=caller_id,
            x_header=sip_header
        )

        if self.machine.callee_channel is None:
            return None

        self.events.callee_created = self.machine.callee_channel.on_event(
            SimpleEvent.Channel.STATE_CHANGE, self.on_callee_channel_created)
        self.events.callee_destroyed = self.machine.callee_channel.on_event(
            SimpleEvent.Channel.DESTROYED, self.on_callee_channel_destroyed)

        self.set_affected_channel_iri(self.machine.callee_channel)
        self.set_affected_channel_icc(self.machine.callee_channel)

        if self.machine.subscription:
            if self.machine.channel.context == ChannelContext.INBOUND:
                Calls.set_call(
                    self.machine.subscription.number,
                    CallDirection.INBOUND
                )
                self.machine.counted_ongoing_call = True
                self.machine.channel.ongoing_call = CallDirection.INBOUND

            # inbound call transferred from another extension
            elif not self.machine.channel.is_endpoint_internal():
                if self.machine.forwarder_app in ('ExtensionCall', 'RingGroup'):
                    Calls.set_call(
                        self.machine.subscription.number,
                        CallDirection.INBOUND
                    )
                    self.machine.counted_ongoing_call = True
                    self.machine.channel.ongoing_call = CallDirection.INBOUND
                elif self.machine.forwarder_app == 'ExternalCall':
                    Calls.set_call(
                        self.machine.subscription.number,
                        CallDirection.OUTBOUND
                    )
                    self.machine.counted_ongoing_call = True
                    self.machine.channel.ongoing_call = CallDirection.OUTBOUND

        if ring_back:
            try:
                self.machine.channel.raw_channel.ring()
            except HTTPError as e:
                logger.error(e)
                self.machine.callee_channel.hangup_channel()

        return self.machine.callee_channel

    def on_call_failure(self):
        self.cleanup()
        self.caller = self.caller.replace("'", "")

        if self.machine.channel.redirect_channel:
            cause = EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
            self.events.playback = Playback(
                channel=self.machine.channel,
                media=settings.DEFAULT_PLAYBACK['call_transfer_failed']
            )
        else:
            cause = EndingCause.CALLEE_DESTROYED

        self.machine.change_state(ExtensionEvent.Callee.DESTROYED, cause=cause)

    def on_callee_channel_destroyed(self, raw_channel, event, cause=EndingCause.CALLEE_DESTROYED):
        self.cleanup()
        self.machine.final_state = event.get('cause_text')
        self.machine.change_state(ExtensionEvent.Callee.DESTROYED, cause=EndingCause.CALLEE_DESTROYED)

    def on_callee_channel_created(self, raw_channel, event):
        if event['channel']['state'] == SimpleEvent.Channel.RINGING:
            print(event)
            print("Callee channel created.")
            self.cleanup()
            self.machine.change_state(ExtensionEvent.Callee.CREATED)

        if event['channel']['state'] == SimpleEvent.Channel.UP:
            print(event)
            print("Callee channel answered.")

            try:
                self.machine.channel.answer()
            except Exception as e:
                logger.error(e)

            self.cleanup()
            self.machine.change_state(SimpleEvent.Channel.TALKING_STARTED)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.next = None
        self.machine.change_state(ExtensionEvent.Caller.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_channel_hangup(self, raw_channel, event):
        print("Caller hangup...")
        self.cleanup()
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.next = None
        self.machine.change_state(ExtensionEvent.Caller.HANGUP, cause=EndingCause.CALLER_HANGUP)

    @staticmethod
    def get_cause(status):
        cause = {
            ExtensionStatus.DISABLE.Value: EndingCause.CALLEE_DISABLED,
            ExtensionStatus.DND.Value: EndingCause.CALLEE_DND,
            ExtensionStatus.OFFLINE.Value: EndingCause.CALLEE_NAVAILABLE
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

    def on_timely_rejection(self):
        self.machine.next = (
            self.machine.extension_webapp.destination_type_off, self.machine.extension_webapp.destination_number_off,
            self.machine.extension_webapp.extension_number, self.machine.subscription)
        self.cleanup()
        self.machine.change_state(SimpleEvent.Base.TIMELY_REJECTION, cause=EndingCause.APP_OUTOFTIME)

    def on_number_in_list(self):
        self.machine.next = (self.machine.extension_webapp.destination_type_in_list,
                             self.machine.extension_webapp.destination_number_in_list,
                             self.machine.extension_webapp.extension_number, self.machine.subscription)
        self.cleanup()
        self.machine.change_state(SimpleEvent.Base.CALLER_RESTRICTED,
                                  cause=EndingCause.APP_CALLER_RESTRICTED)

    def enter(self):
        local_caller = self.machine.channel.get_variable('X-ISLOCALBACK')
        if local_caller is not None:
            if local_caller == 'True':
                self.machine.local_caller = True

        if (
                self.machine.channel.intent == ChannelIntent.CALL and
                self.machine.channel.context != ChannelContext.INTERNAL and
                self.machine.subscription
        ):

            calls = Calls.get_calls_by_number(
                self.machine.subscription.number
            )

            if calls >= self.machine.subscription.max_call_concurrency:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
                )
                self.cleanup()
                self.machine.change_state(
                    SimpleEvent.Call.MAX_CONCURRENCY,
                    cause=EndingCause.MAX_CALL_CONCURRENCY
                )

                return

        if self.machine.extension_webapp.status == ExtensionStatus.DND:
            print("Target status is DND")
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.BEGIN,
                affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
            )
            self.cleanup()
            self.machine.change_state(
                ExtensionEvent.Callee.DESTROYED,
                cause=self.get_cause(ExtensionStatus.DND.Value)
            )

            return

        elif (
                self.machine.extension_webapp.status ==
                                                    ExtensionStatus.DISABLE or
                self.machine.extension_webapp.status ==
                                                    ExtensionStatus.OFFLINE
        ):
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.BEGIN,
                affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
            )
            self.cleanup()
            self.machine.change_state(
                ExtensionEvent.Callee.DESTROYED,
                cause=self.get_cause(self.machine.extension_webapp.status)
            )

            return

        elif self.machine.extension_webapp.status == ExtensionStatus.FORWARD:
            if self.machine.extension_webapp.forward_to:
                print(
                    "Target status is FORWARD, Forwarding to: %s"
                    % self.machine.extension_webapp.forward_to
                )

                self.cleanup()
                self.machine.next = (
                    CallApplicationType.renew,
                    self.machine.extension_webapp.forward_to,
                    self.machine.channel,
                    "blind",
                    self.machine.extension_webapp.extension_number
                )
                self.machine.change_state(
                    ExtensionEvent.Caller.BTRANSFERRED,
                    cause=EndingCause.CALLER_TRANSFERRED
                )

                return

            else:
                print(
                    "Target status is FORWARD, bad forward number. hanging up."
                )
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
                )
                self.cleanup()
                self.machine.change_state(
                    ExtensionEvent.Callee.DESTROYED,
                    cause=EndingCause.CALLEE_DESTROYED
                )

                return

        elif self.machine.extension_webapp.status != ExtensionStatus.AVAILABLE:
            print(
                "Target status is not reliable: %s"
                % self.machine.extension_webapp.status
            )
            self.machine.channel.send_packet(
                packet_type=IRIConstants.Record.BEGIN,
                affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
            )
            self.cleanup()
            self.machine.change_state(
                ExtensionEvent.Callee.DESTROYED,
                cause=self.get_cause(self.machine.extension_webapp.status)
            )

            return

        else:
            if self.machine.waiting_call:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    affected_number=normalize_outbound_number(
                                        self.machine.channel.source_number),
                    supps_type={
                        'service_action': IRIConstants.SERVICE_ACTION.ACTIVATION,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.CW,
                        'party_number': self.machine.channel.destination_number,
                        },
                        )
            else:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
                )

            if self.machine.channel.endpoint_number == \
                                    self.machine.channel.destination_number:
                self.machine.channel.send_packet(
                    packet_type=IRIConstants.Record.BEGIN,
                    affected_number=normalize_outbound_number(
                                            self.machine.channel.source_number)
                )
                self.cleanup()
                self.machine.change_state(
                    ExtensionEvent.Callee.DESTROYED,
                    cause=EndingCause.CALLEE_NEXISTS
                )

                return

            print(
                "Target status is: %s".format(
                    self.machine.extension_webapp.status,
                )
            )

            # conditional list check
            caller = self.machine.channel.source_number
            if hasattr(self.machine.extension_webapp, 'conditional_list'):
                if self.machine.extension_webapp.conditional_list:
                    if self.machine.extension_webapp.conditional_list.is_number_in_list(caller):
                        self.on_number_in_list()

                        return

            self.events.channel_destroyed = \
                self.machine.channel.raw_channel.on_event(
                    SimpleEvent.Channel.DESTROYED,
                    self.on_channel_destroyed
                )
            self.events.channel_hangup = \
                self.machine.channel.raw_channel.on_event(
                    SimpleEvent.Channel.HANGUP_REQUEST,
                    self.on_channel_hangup
                )

            if self.handlers.bridge is None:
                self.handlers.bridge = Bridge.create_bridge(BridgeType.MIXING)

            if self.machine.caller_extension is None:
                try:
                    internal_extension = Extension.objects.get(
                        extension_number__number=
                        self.machine.channel.source_number
                    )
                    if internal_extension.subscription:
                        self.caller = str(
                            normalize_outbound_number(
                                internal_extension.subscription.number
                            )
                        )
                except Extension.DoesNotExist:
                    self.caller = str(self.machine.channel.source_number)
            else:
                if self.machine.forwarder_number:
                    self.caller = "%s <%s>" % (
                        self.machine.caller_extension.user.ascii_name,
                        self.machine.forwarder_number
                    )
                else:
                    self.caller = "%s <%s>" % (
                        self.machine.caller_extension.user.ascii_name,
                        self.machine.channel.source_number
                    )

            print(
                "Setting up a call from %s to %s" % (
                    self.caller, self.machine.target_number
                )
            )

            if self.__call_to(
                    ring_back=self.machine.ring_back,
                    caller_id=self.caller
            ) is None:
                self.on_call_failure()

    def __str__(self):
        return SetupState.state_name
