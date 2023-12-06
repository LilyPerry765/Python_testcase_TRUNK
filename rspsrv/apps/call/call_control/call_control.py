# !/usr/bin/env python
import logging
import time
import uuid
from threading import Timer

import requests
from django.conf import settings
from requests import HTTPError

from rspsrv.apps.call.apps.base import (
    BaseCallApplication,
    EndingCause,
    CDRAction,
)
from rspsrv.apps.call.apps.base import CallApplicationType, SimpleEvent
from rspsrv.apps.call.apps.date_time_vr.core import DateTimeVR
from rspsrv.apps.call.apps.defaults.ivr import (
    ExtensionPlayback,
    ExternalPlayback,
)
from rspsrv.apps.call.apps.ext_dispatcher.core import ExtDispatcher
from rspsrv.apps.call.apps.extension_call.core import ExtensionCall
from rspsrv.apps.call.apps.external_call.core import ExternalCall
from rspsrv.apps.call.apps.fax_receive.core import FaxReceive
from rspsrv.apps.call.apps.playback.core import Playback
from rspsrv.apps.call.apps.status.core import ExtensionStatus
from rspsrv.apps.call.call_control.types import CallState
from rspsrv.apps.cdr.models import CDR
from rspsrv.apps.extension.models import ExtensionNumber, Extension
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.utils import (
    normalize_outbound_number,
    is_number_international,
)
from rspsrv.tools.utility import Helper
from .base import get_call_pool
from .bridge import BridgeType, Bridge
from .call_pool import LI
from .channel import Channel, ChannelFlow, ChannelContext, ChannelIntent
from .icc import ICCManager
from .iri import IRIManager
from .spy import Interception
from .statics import DefaultCallManagerPool
from ..utils import timer_hangup

logger = logging.getLogger("call")


class CallManager(object):
    def __init__(self):
        self.channels = []
        self.spy_channels = []
        self.caller_channels = {}

        self.spy_bridge = None
        self.main_bridge = None
        self.snoop_channel = None

        # Control creation time
        self.start_time = time.time()

        # Control unique identifier
        self.control_id = uuid.uuid4()

        # Create main bridge
        self.main_bridge = Bridge.create_bridge(bridge_type=BridgeType.MIXING,
                                                name='main_bridge_%s' % self.control_id)

        self.hold_bridge = Bridge.create_bridge(bridge_type=BridgeType.HOLD,
                                                name='hold_bridge_%s' % self.control_id)
        # Create spy bridge
        self.spy_bridge = Bridge.create_bridge(bridge_type=BridgeType.MIXING,
                                               name='spy_bridge_%s' % self.control_id)

        self.spy_iri = []
        self.spy_icc = []

        self.originator_user = None
        self.terminator_users = {}

        self.onhold_users = {}
        call_pool = get_call_pool()
        call_pool.append(self)

    def hold_user(self, user):
        for channel in self.channels:
            if (channel.originator_user == user and channel.flow == ChannelFlow.OUTGOING) or (
                    channel.terminator_user == user and channel.flow == ChannelFlow.INCOMING):
                self.onhold_users[user] = channel
                self._remove_channel_from_bridge(channel)
                self._add_channel_to_bridge(channel, hold=True)
                return channel

    def unhold_user(self, user):
        channel = self.onhold_users.pop(user, None)
        if channel is None:
            return False
        self._remove_channel_from_bridge(channel, hold=True)
        self._add_channel_to_bridge(channel)
        return channel

    def register_raw_channel(self, channel, flow, billing=False):
        call_manager_channel = Channel(channel, flow, billing_cb=self.billing_cb if billing else None)
        self.register_channel(call_manager_channel, flow)
        return call_manager_channel

    def billing_cb(self, channel, duration):
        if channel in self.channels:
            self._kill(channel)

    def register_channel(self, call_manager_channel, flow, spy=False):
        """
        :param spy:
        :param call_manager_channel: CallManagerChannel object
         :type call_manager_channel: CallManagerChannel
        :param flow: Channel Flow
         :type flow: ChannelFlow
        :return: None
        """
        if flow == ChannelFlow.INCOMING:
            call_manager_channel.raw_channel.answer()
            Timer(
                settings.MAX_CALL_DURATION_SECONDS,
                timer_hangup,
                [call_manager_channel],
            ).start()

        if not self._add_channel_to_bridge(
                channel=call_manager_channel,
                spy=spy
        ):
            logger.info("Channel %s added to bridge" % call_manager_channel.uid)

            return None

        if spy:
            self.spy_channels.append(call_manager_channel)
        else:
            self.channels.append(call_manager_channel)

    def unregister_channel(self, call_manager_channel, flow, spy=False):
        """
        :param spy:
        :param call_manager_channel: CallManagerChannel object
         :type call_manager_channel: CallManagerChannel
        :param flow: Channel Flow
         :type flow: ChannelFlow
        :return: None
        """
        if self._remove_channel_from_bridge(
                channel=call_manager_channel,
                spy=spy
        ):

            return None

        if spy:
            self.spy_channels.remove(call_manager_channel)
        else:
            self.channels.remove(call_manager_channel)

        if flow == ChannelFlow.INCOMING:
            call_manager_channel.hangup_channel()

    def call_to(
            self,
            target_number,
            caller_channel,
            app_args='dialing',
            ring_back=True,
            bill=True
    ):
        # create new channel
        callee_channel = Channel.create_channel(
            target_number,
            app_args,
            originator=caller_channel,
            billing_cb=self.billing_cb if bill else None
        )
        if callee_channel is None:
            logger.info("Whoops, pretty sure %s wasn't valid" % target_number)

            return None

        if ring_back:
            caller_channel.raw_channel.ring()

        self.caller_channels.update({str(callee_channel.uid): caller_channel})

        caller_channel.raw_channel.on_event(
            'StasisEnd',
            lambda *args: self._end_caller_channel(
                caller_channel,
                callee_channel
            )
        )

        callee_channel.raw_channel.on_event(
            'StasisStart',
            lambda *args: self._complete_outgoing_channel(
                caller_channel,
                callee_channel
            )
        )
        callee_channel.raw_channel.on_event(
            'StasisEnd',
            lambda *args: self._end_callee_channel(
                caller_channel,
                callee_channel
            )
        )
        callee_channel.raw_channel.on_event(
            'ChannelDestroyed',
            lambda *args: self._end_callee_channel(
                caller_channel,
                callee_channel
            )
        )

        return callee_channel

    def _add_channel_to_bridge(self, channel, spy=False, hold=False):
        try:
            if spy:
                self.spy_bridge.bridge.addChannel(channel=channel.raw_channel.id)
            elif hold:
                self.hold_bridge.bridge.addChannel(channel=channel.raw_channel.id)
            else:
                self.main_bridge.bridge.addChannel(channel=channel.raw_channel.id)
            return True
        except requests.HTTPError:
            return False

    def _remove_channel_from_bridge(self, channel, spy=False, hold=False):
        try:
            if spy:
                self.spy_bridge.bridge.removeChannel(
                    channel=channel.raw_channel.id
                )
            elif hold:
                self.hold_bridge.bridge.removeChannel(
                    channel=channel.raw_channel.id
                )
            else:
                self.main_bridge.bridge.removeChannel(
                    channel=channel.raw_channel.id
                )
        except requests.HTTPError as error:
            logger.error(error)

        if len(self.channels) == 0:
            self.main_bridge.destroy()
            self.spy_bridge.destroy()
            try:
                call_pool = get_call_pool()
                call_pool.remove(self)
            except Exception as error:
                logger.error(error)

        return True

    def _killall(self):
        for channel in self.channels:
            self._kill(channel)

    def _kill(self, channel):
        channel.hangup_channel()
        if channel in self.channels:
            self.unregister_channel(channel, channel.flow)

    def _complete_outgoing_channel(self, caller_channel, callee_channel, spy=False):
        self.register_channel(callee_channel, callee_channel.flow, spy=spy)
        if not spy:
            caller_channel.start_billing()
        caller_channel.raw_channel.answer()
        Timer(
            settings.MAX_CALL_DURATION_SECONDS,
            timer_hangup,
            [caller_channel],
        ).start()
        for iri in self.spy_iri:
            iri.set_state_connected()
            iri.set_record_continue()

    def _complete_outgoing_spy_channel(self, caller_channel, callee_channel, spy=False):
        self.register_channel(callee_channel, callee_channel.flow, spy=spy)

    def _end_caller_channel(self, caller_channel, callee_channel):
        if caller_channel in self.channels:
            self.channels.remove(caller_channel)
        if len(self.channels) < 2 and callee_channel:
            self._kill(callee_channel)
        caller_channel.stop_billing()
        self._remove_channel_from_bridge(caller_channel)
        for iri in self.spy_iri:
            if caller_channel == iri.target_channel:
                iri.set_record_end()
                self.spy_iri.remove(iri)
        for icc in self.spy_icc:
            if caller_channel == icc.target_channel:
                icc.destroy()
                self.spy_icc.remove(icc)

    def _end_callee_channel(self, caller_channel, callee_channel):
        print(self.channels)
        if callee_channel in self.channels:
            self.channels.remove(callee_channel)
        print("LEN: ", len(self.channels))
        if len(self.channels) == 1:
            self._kill(caller_channel)
        caller_channel.stop_billing()
        self._remove_channel_from_bridge(caller_channel)
        for iri in self.spy_iri:
            if callee_channel == iri.target_channel:
                iri.set_record_end()
                self.spy_iri.remove(iri)
        for icc in self.spy_icc:
            if caller_channel == icc.target_channel:
                icc.destroy()
                self.spy_icc.remove(icc)

    def destroy(self):
        self._killall()


def init_spying(call_manager, caller_channel, callee_channel):
    caller_li_data = []
    Interception.check_for_spy(caller_channel.source_number)
    callee_li_data = []  # Interception.check_for_spy(caller_channel.destination_number)

    li_data = caller_li_data + callee_li_data
    for li in li_data:
        print("LI: ", li)
    if len(li_data):
        # LI.total_spied_calls += 1 # NOT USED ANY-WHERE!
        make_spy_iri_on_channel(call_manager, caller_channel, caller_li_data)
        make_spy_iri_on_channel(call_manager, callee_channel, callee_li_data)

    # li_data = caller_li_data + callee_li_data
    if len(li_data):
        make_spy_calls_on_channel(call_manager, caller_channel, li_data)


def make_spy_iri_on_channel(call_manager, channel, li_data):
    if channel is None:
        return
    for d in li_data:
        iri = IRIManager(target_channel=channel, li_data=d)
        call_manager.spy_iri.append(iri)
    print("----LIDATA----", li_data)


def make_spy_calls_on_channel(call_manager, channel, li_data):
    if channel is None:
        return
    for d in li_data:
        if d.interception_type != "IRI only":
            icc = ICCManager(target_channel=channel, li_data=d)
            call_manager.spy_icc.append(icc)


def stasis_start_cb(channel_obj, ev):
    raw_channel = channel_obj.get('channel')
    raw_channel_name = raw_channel.json.get('name')
    args = ev.get('args')

    if not args:
        logger.error(
            "Error: {} didn't provide any arguments!".format(raw_channel_name)
        )

        return

    logger.info(args)

    if args and args[0] != 'incoming':
        # Only handle inbound channels here
        return

    if len(args) != 2:
        logger.error(
            "Error: {} didn't tell us who to dial".format(raw_channel_name)
        )

        return

    print("New incoming call")
    call = CallManager()
    print("Call control created")
    caller_channel = call.register_raw_channel(
        raw_channel, ChannelFlow.INCOMING,
        billing=True
    )

    callee_number = args[1]

    # check for spying
    logger.info("Spying number:{}".format(callee_number))

    # call to callee
    callee_channel = None
    if caller_channel.alive:
        callee_channel = call.call_to(
            target_number=callee_number,
            caller_channel=caller_channel
        )
        if caller_channel is None:
            logger.error("ERROR CALLER CHANNEL IS NONE")

    init_spying(call, caller_channel, callee_channel)


def get_call_app(app_type):
    call_app_map = {
        CallApplicationType.EXTENSION: ExtensionCall,
        CallApplicationType.EXTERNAL: ExternalCall,
        CallApplicationType.FAX: FaxReceive,
        CallApplicationType.STATUS: ExtensionStatus,
        CallApplicationType.DATE_TIME_VR: DateTimeVR,
        CallApplicationType.EXTENSION_DISPATCHER: ExtDispatcher,
        CallApplicationType.PLAYBACK: Playback
    }

    return call_app_map.get(app_type, None)


class CallControl(object):
    SubscriptionDefaultManager = None
    call_id = 0

    def __init__(self, state=None):
        self.state = state if state else CallState.SETUP
        self.app_history = []
        self.current_app = None
        self.channel = None
        self.next = None

        self.current_target_number = None
        self.current_app_type = None

        self.cdr = None
        self.start_time = time.time()
        self.end_time = time.time()
        self.duration = 0
        self.talk_time = 0

        self.recorded_audio = None

        self.conferenced = False

    def __call_app_setup(self, app, caller_channel, target_number, **kwargs):
        print("App: ", app)
        try:
            if 'call_id' in kwargs:
                app_instance = app(caller_channel=caller_channel, target_number=target_number, **kwargs)
            else:
                if app == get_call_app(app_type=CallApplicationType.PLAYBACK):
                    app_instance = app(channel=caller_channel, target_number=target_number,
                                       call_id=caller_channel.call_id, **kwargs)
                else:
                    app_instance = app(caller_channel=caller_channel, target_number=target_number,
                                       call_id=caller_channel.call_id, **kwargs)
        except (BaseCallApplication.WebAppNotExists, BaseCallApplication.WebAppRestriction):
            raise
        return app_instance

    def __call_app_on_exit(self, **kwargs):
        print(self.app_history)

        transferred_causes = [
            EndingCause.CALLEE_ATRANSFERRED,
            EndingCause.CALLER_ATRANSFERRED,
            EndingCause.CALLEE_TRANSFERRED,
            EndingCause.CALLER_TRANSFERRED
        ]

        renew_call = False
        cdr_action = kwargs.pop('cdr_action', None)
        cause = kwargs.pop('cause', None)
        next = kwargs.pop('next', None)
        endpoint_type = kwargs.pop('endpoint_type', None)
        endpoint_name = kwargs.pop('endpoint_name', None)

        if cause in transferred_causes:
            cdr_action = CDRAction.TRANSFERRED

        self.duration += self.current_app.get_duration()

        recorded_audio_name = None
        if hasattr(self.current_app, 'get_recorded_audio_name'):
            recorded_audio_name = self.current_app.get_recorded_audio_name()
        self.recorded_audio = None
        if recorded_audio_name:
            self.recorded_audio = "cdr/{call_id}/{recorded_audio_name}".format(
                call_id=self.cdr.call_id,
                recorded_audio_name=recorded_audio_name
            )
            self.recorded_audio.replace(".", "_")
            self.recorded_audio += '.wav'

        if hasattr(self.current_app, 'talking_time'):
            self.talk_time += self.current_app.get_talk_time()

        self.app_history[-1][1] = cause

        if next is not None:
            if next[0] != CallApplicationType.end:
                if next[0] == CallApplicationType.renew:
                    renew_call = True
                    self.end_time = time.time()
                    if hasattr(self.current_app, 'agent_number'):
                        call_app_agent = self.current_app.agent_number
                        parent = self.current_app.extension_number
                    else:
                        call_app_agent = None
                        parent = None
                    self.cdr.close_record(
                        duration=self.duration,
                        talk_time=self.talk_time,
                        recorded_audio=self.recorded_audio,
                        end_cause=cause,
                        agent=call_app_agent,
                        parent=parent,
                        cdr_action=cdr_action,
                        caller_extension_endpoint_type=endpoint_type,
                        caller_extension_endpoint_name=endpoint_name
                    )
                    if next[3] == "blind":
                        self.channel.events_unsubscriber()

                        forwarder_extension = None
                        forwarder_app = None
                        if len(next) > 4:
                            forwarder_extension = next[4]
                            forwarder_app = type(self.current_app)

                        forwarder_subscription = None
                        if hasattr(self.current_app, 'subscription'):
                            forwarder_subscription = \
                                self.current_app.subscription

                        CallControl.io_channel_callback(
                            {
                                'channel': next[2].raw_channel,
                                'call_id': next[2].call_id,
                                'spy_iccs': next[2].keep_safe_spy_iccs or
                                            next[2].spy_iccs,
                                'spy_iris': next[2].spy_iris,
                                'billing_control': next[2].billing_control
                            },
                            None,
                            is_transferred=next[2].is_transferred,
                            args=[
                                ChannelFlow.REDIRECT,
                                next[1],
                                "unknown",
                                "unknown",
                                "none"
                            ],
                            forwarder_extension=forwarder_extension,
                            subscription=forwarder_subscription,
                            forwarder_app=forwarder_app
                        )

                        next[2].keep_safe_spy_iccs = []
                    elif next[3] == "attended":
                        pass
                    elif next[3] == "fax-in":
                        pass
                elif next[0] == CallApplicationType.current:
                    self.call_loop(self.channel,
                                   extension=(
                                       self.current_app_type,
                                       self.current_target_number
                                   ),
                                   renewed=True, **kwargs
                                   )

                    return
                elif next[0] is None:
                    self.call_loop(
                        self.channel,
                        target_number=next[1],
                        renewed=True,
                        **kwargs
                    )

                    return
                else:
                    self.call_loop(
                        self.channel,
                        extension=next,
                        call_id=self.cdr.call_id,
                        renewed=True, **kwargs
                    )

                    return

        print("Cause: %s, Duration: " % cause, self.duration)
        self.end_time = time.time()

        if hasattr(self.current_app, 'agent_number'):
            call_app_agent = self.current_app.agent_number
            parent = self.current_app.extension_number
        else:
            call_app_agent = None
            parent = None
        self.cdr.close_record(
            duration=self.duration,
            talk_time=self.talk_time,
            recorded_audio=self.recorded_audio,
            end_cause=cause,
            agent=call_app_agent,
            parent=parent,
            cdr_action=cdr_action,
            caller_extension_endpoint_type=endpoint_type,
            caller_extension_endpoint_name=endpoint_name
        )

        if (
                self.channel.intent == ChannelIntent.CALL and
                not renew_call and
                not self.conferenced
        ):
            print(
                "Control will kill the caller...",
                cause,
                "Intent:",
                self.channel.intent
            )
            self.channel.hangup()
        elif self.channel.intent != ChannelIntent.CALL:
            if self.channel.intent != ChannelIntent.TRANSFERRING:
                self.channel.intent = ChannelIntent.CALL

    def __call_app_on_enter(self, **kwargs):
        history = kwargs.pop('history', None)
        print("Call app on enter. history: ", history)

    def __call_app_on_termination(self):
        self.end_time = time.time()
        self.cdr.close_record(duration=self.duration, end_cause=SimpleEvent.Application.TERMINATED)

        self.channel.hangup_channel()

    def call_loop(self, channel, target_number=None, extension=None, **kwargs):
        if 'cdr' not in kwargs:
            kwargs.update({'cdr': self.cdr})

        if target_number is None and extension is None:
            channel.hangup_channel()

            return
        forwarder_extension = kwargs.get('forwarder_extension', None)

        app_instance = None
        app_type = None
        renewed = kwargs.pop('renewed', False)

        if extension:
            app_type = extension[0]
            target_number = extension[1]
            forwarder_subscription = None
            if len(extension) > 3:
                kwargs.update({'subscription': extension[3]})
                forwarder_subscription = extension[3].number
            if len(extension) > 2:
                kwargs.update({'forwarder_extension': extension[2]})
                if app_type == CallApplicationType.EXTERNAL:
                    target_number = normalize_outbound_number(
                        target_number,
                        forwarder_subscription
                    )

            if (
                    renewed and
                    not (
                            app_type == CallApplicationType.AUTH_IVR or
                            app_type == CallApplicationType.INBOX_PLAY
                    )
            ):
                self.cdr.call_renewed(target_number)
            app_instance = self.__call_app_setup(
                app=get_call_app(app_type=app_type),
                caller_channel=self.channel,
                target_number=target_number, **kwargs
            )
            print(get_call_app(app_type), app_instance)
        elif target_number:
            try:
                extension = ExtensionNumber.objects.get(number=target_number)
                app_type = extension.type

                app_instance = self.__call_app_setup(
                    app=get_call_app(app_type=app_type),
                    caller_channel=self.channel,
                    target_number=target_number,
                    **kwargs
                )
                if forwarder_extension:
                    self.cdr.set_extensions(
                        caller_extension=forwarder_extension.number
                    )

            except ExtensionNumber.DoesNotExist:
                app_instance = ExtensionPlayback.not_exists(
                    channel=self.channel
                )

        self.current_target_number = target_number
        self.current_app_type = app_type
        self.current_app = app_instance
        self.app_history.append([self.current_app.get_name(), None])

        if app_instance is None:
            self.__call_app_on_termination()

            return

        app_instance.on_event(
            SimpleEvent.Application.STARTED,
            self.__call_app_on_enter
        )
        app_instance.on_event(
            SimpleEvent.Application.TERMINATED,
            self.__call_app_on_termination
        )
        app_instance.on_event(
            SimpleEvent.Application.FINISHED,
            self.__call_app_on_exit
        )

        if self.current_app_type == CallApplicationType.EXTENSION:
            self.cdr.set_extensions(called_extension=target_number)
        elif self.current_app_type == CallApplicationType.RECEPTIONIST:
            self.cdr.set_parent(target_number)

        app_instance.enter()

    def __call_transfer_check(self, machine_history):
        last_event, last_state = machine_history[-1]

        if hasattr(self.current_app.app_states, 'transferring'):
            if last_state == self.current_app.app_states.transferring:
                CallControl.io_channel_callback(
                    None,
                    None,
                    args=[
                        ChannelFlow.REDIRECT,
                        last_state.target_number,
                        ChannelIntent.TRANSFER
                    ],
                    channel=last_state.transferor
                )

    def __call_conference_check(self, machine_history, **kwargs):
        last_event, last_state = machine_history[-1]

        if hasattr(self.current_app.app_states, 'conferencing'):
            if last_state == self.current_app.app_states.conferencing:
                self.conferenced = True

                CallControl.io_channel_callback(
                    None,
                    None,
                    args=[
                        ChannelFlow.INCOMING,
                        last_state.target_number,
                        ChannelIntent.CONFERENCE
                    ],
                    channel=last_state.machine.channel
                )

    def serve_internal_call(self, channel, target_number, **kwargs):
        forwarder_extension = kwargs.pop('forwarder_extension', None)
        print("Serving an Internal Call")
        print("Creating CDR record...")

        rate = 0.0
        self.cdr = CDR.init_internal_record(
            channel=channel,
            call_id=channel.call_id,
            rate=rate
        )

        self.channel = channel

        self.call_loop(
            self.channel,
            target_number=target_number,
            call_id=self.cdr.call_id,
            forwarder_extension=forwarder_extension,
            subscription=self.SubscriptionDefaultManager,
            cdr=self.cdr,
            **kwargs
        )

    # Deprecated
    # def serve_incoming_fax(self, channel, target_number):
    #     print("Serving an Fax Call")
    #     print("Creating CDR record...")
    #
    #     rate = 0.0
    #     self.cdr = CDR.init_fax_record(
    #         channel=channel,
    #         call_id=channel.call_id,
    #         fax_target_number=target_number,
    #         rate=rate
    #     )
    #     self.channel = channel
    #     self.call_loop(self.channel, target_number=target_number)

    def serve_inbound_call(self, channel, target_number):
        print("Serving an Inbound Call")

        if not self.SubscriptionDefaultManager.activation:
            return

        if not self.SubscriptionDefaultManager.call_is_allowed(channel):
            self.channel.hangup_channel()
            return

        mask_number = channel.get_variable('P-Asserted-Identity')
        channel.set_mask_number(mask_number)

        rate = 0.0
        self.cdr = CDR.init_call_record(
            channel=channel,
            call_id=channel.call_id,
            rate=rate,
            caller=normalize_outbound_number(channel.endpoint_number),
            called=normalize_outbound_number(channel.destination_number),
            mask_number=mask_number
        )
        self.channel = channel

        if settings.LI_ENABLED:
            self.channel.li_data = Interception.check_for_spy(
                self.SubscriptionDefaultManager.number
            )

            if self.channel.li_data:
                for d in self.channel.li_data:
                    LI.increase_cin()

                    iri = IRIManager(
                        target_channel=self.channel,
                        li_data=d,
                        call_id=channel.call_id,
                        subscription_number=self.SubscriptionDefaultManager
                            .number,
                        active=False,
                        affected_number=normalize_outbound_number(
                            self.channel.source_number
                        )
                    )
                    self.channel.spy_iris.append(iri)

                    icc = ICCManager(
                        target_channel=self.channel,
                        li_data=d,
                        active=True,
                        call_id=channel.call_id,
                    )
                    self.channel.spy_iccs.append(icc)

        extension = self.SubscriptionDefaultManager.get_destination()
        target_number = extension[1]
        end_cause = "route_to_end"

        if extension[0] == CallApplicationType.end:
            self.cdr.close_record(duration=self.duration, end_cause=end_cause)
            self.channel.hangup()
        elif extension[0] == CallApplicationType.EXTERNAL:
            extension = (
                CallApplicationType.EXTERNAL,
                normalize_outbound_number(target_number)
            )
            self.call_loop(
                self.channel,
                extension=extension,
                call_id=channel.call_id,
                cdr=self.cdr
            )
        else:
            self.call_loop(
                self.channel,
                target_number=target_number,
                call_id=channel.call_id,
                subscription=self.SubscriptionDefaultManager,
                cdr=self.cdr
            )

    def serve_outbound_call(self, channel, target_number, **kwargs):
        print("Serving an Outbound Call")

        if not self.SubscriptionDefaultManager.activation:
            try:
                channel.answer()
            except HTTPError as e:
                logger.error(e)

            playback = ExternalPlayback.call_not_possible(
                channel,
                cause=EndingCause.SUBSCRIPTION_DEACTIVATED,
            )
            playback.enter()
            return

        if not self.SubscriptionDefaultManager.allow_outbound:
            try:
                channel.answer()
            except HTTPError as e:
                logger.error(e)

            playback = ExternalPlayback.outbound_disabled(
                channel,
                cause=EndingCause.OUTBOUND_DISABLED,
            )
            playback.enter()
            return

        forwarder_extension = kwargs.pop('forwarder_extension', None)
        if not self.SubscriptionDefaultManager.call_is_allowed(channel):
            channel.hangup_channel()
            return

        rate = 0.0

        if is_number_international(target_number):
            if not self.SubscriptionDefaultManager.international_call:
                channel.hangup_channel()
                return
            callee = target_number
        else:
            callee = normalize_outbound_number(
                target_number,
                self.SubscriptionDefaultManager.number
            )

        extension = (CallApplicationType.EXTERNAL, callee)
        channel.destination_number = target_number
        print("Extension: ", extension)

        self.cdr = CDR.init_call_record(
            channel=channel,
            call_id=channel.call_id,
            rate=rate,
            caller=normalize_outbound_number(
                self.SubscriptionDefaultManager.number
            ),
            called=callee
        )
        # called=normalize_outbound_number(channel.destination_number))
        if forwarder_extension:
            self.cdr.set_extensions(
                caller_extension=forwarder_extension.number
            )
        else:
            self.cdr.set_extensions(caller_extension=channel.endpoint_number)

        self.call_id += 1
        self.channel = channel

        if settings.LI_ENABLED:
            '''
            Prevent from Create Duplicate ICCs/IRIs when this Call Is 
            Transferred or Conference Call (ICCs/IRIs already Created).
            '''
            if not forwarder_extension:
                self.channel.li_data = Interception.check_for_spy(
                    self.SubscriptionDefaultManager.number
                )

                if self.channel.li_data:
                    for d in self.channel.li_data:
                        LI.increase_cin()

                        iri = IRIManager(
                            target_channel=self.channel,
                            li_data=d,
                            subscription=self.SubscriptionDefaultManager,
                            call_id=channel.call_id,
                            subscription_number=
                            self.SubscriptionDefaultManager.number,
                            active=False,
                            affected_number=normalize_outbound_number(
                                self.channel.destination_number
                            ),
                        )
                        self.channel.spy_iris.append(iri)

                        icc = ICCManager(
                            target_channel=self.channel,
                            li_data=d,
                            active=True,
                            call_id=channel.call_id,
                        )
                        self.channel.spy_iccs.append(icc)

        self.call_loop(
            self.channel,
            extension=extension,
            subscription=self.SubscriptionDefaultManager,
            call_id=channel.call_id,
            forwarder_extension=forwarder_extension,
            timeout=settings.EXTERNAL_CALL_RINGING_TIMEOUT,
            cdr=self.cdr
        )

    def serve_feature_call(self, channel, target_number):
        channel.hangup_channel()

        return

    @staticmethod
    def io_channel_callback(channel_object, event, args=None, **kwargs):
        raw_channel = None
        call_id = None
        spy_iccs = []
        spy_iris = []
        billing_control = None

        if channel_object:
            raw_channel = channel_object.get('channel')
            call_id = channel_object.get('call_id', None)
            spy_iccs = channel_object.get('spy_iccs', [])
            spy_iris = channel_object.get('spy_iris', [])
            billing_control = channel_object.get('billing_control', None)

        channel = kwargs.get('channel', None)
        CallControl.SubscriptionDefaultManager = kwargs.get(
            'subscription',
            None,
        )

        if not spy_iccs and channel and hasattr(channel, 'spy_iccs'):
            spy_iccs = getattr(channel, 'spy_iccs', [])
        if not spy_iris and channel and hasattr(channel, 'spy_iris'):
            spy_iris = getattr(channel, 'spy_iris', [])
        if not billing_control and channel and hasattr(channel,
                                                       'billing_control'):
            billing_control = getattr(channel, 'billing_control', None)

        if args is None:
            args = event.get('args')
        print(args)

        if channel is None and len(args) < 5:
            print("Error: Incorrect arguments")
            return

        if args and args[0] != 'incoming' and args[0] != 'redirect':
            print(args)
            return

        flow = args[0]
        target_number = args[1]
        intent = ChannelIntent.CALL
        channel_is_transferred = kwargs.pop('is_transferred', False)
        forwarder_extension = kwargs.pop('forwarder_extension', None)
        forwarder_app = kwargs.pop('forwarder_app', None)
        if forwarder_app == ExtensionCall:
            forwarder_app = 'ExtensionCall'
        elif forwarder_app == ExternalCall:
            forwarder_app = 'ExternalCall'

        call = CallControl()

        if channel:
            channel.context = ChannelContext.UNKNOWN
            context = channel.context
            trunk_name = None
            intent = args[2]
            call.conferenced = channel.intent == ChannelIntent.CONFERENCE
        else:
            context = args[2]
            trunk_name = args[3]

        print(
            "Flow: %s, Target_Number: %s, Context: %s, Trunk: %s" % (
                flow,
                target_number,
                context,
                trunk_name
            )
        )
        if (
                (
                        flow == ChannelFlow.INCOMING or
                        flow == ChannelFlow.REDIRECT
                ) and
                context == ChannelContext.FEATURE
        ):
            caller_channel = channel or Channel(
                raw_channel,
                channel_flow=flow,
                channel_context=ChannelContext.FEATURE,
                target_number=target_number, channel_intent=intent
            )

            caller_channel.call_id = \
                call_id or DefaultCallManagerPool.issue_call_id(caller_channel)
            call.serve_feature_call(caller_channel, target_number)

            return call
        if (
                (
                        flow == ChannelFlow.INCOMING or
                        flow == ChannelFlow.REDIRECT
                ) and
                context == ChannelContext.INBOUND
        ):
            caller_channel = channel or Channel(
                raw_channel,
                channel_flow=flow,
                channel_context=ChannelContext.INBOUND,
                target_number=target_number,
                channel_intent=intent
            )
            caller_channel.call_id = \
                call_id or DefaultCallManagerPool.issue_call_id(caller_channel)

            try:
                CallControl.SubscriptionDefaultManager = \
                    Subscription.objects.get_default(
                        Helper.normalize_number(
                            target_number,
                        )
                    )
            except Subscription.DoesNotExist:
                return
            call.serve_inbound_call(caller_channel, target_number)

            return call

        if (
                (
                        flow == ChannelFlow.INCOMING or
                        flow == ChannelFlow.REDIRECT
                ) and
                (
                        context == ChannelContext.UNKNOWN or
                        context == ChannelContext.INTERNAL
                )
        ):
            extension = None

            if forwarder_extension:
                try:
                    extension = forwarder_extension.extension
                except Exception:
                    try:
                        extension_number = ExtensionNumber.objects.get(
                            number=forwarder_extension
                        )
                        extension = extension_number.extension
                        forwarder_extension = extension_number
                    except Exception as error:
                        logger.error(error)

            # else:
            if not extension:
                try:
                    extension_number = ExtensionNumber.objects.get(
                        number=channel.extension_number if channel else
                        raw_channel.json['caller']['number'])
                    print("EXTENSION NUMBER:", extension_number)
                    extension = extension_number.extension
                    print("EXTENSION:", extension)

                except (
                        Extension.DoesNotExist,
                        Extension.MultipleObjectsReturned,
                        ExtensionNumber.DoesNotExist,
                        ExtensionNumber.MultipleObjectsReturned
                ) as error:
                    logger.error(error)
                    if raw_channel:
                        raw_channel.hangup()
                    if channel:
                        channel.hangup()

                    return

            if extension.subscription:
                CallControl.SubscriptionDefaultManager = extension.subscription

                if CallControl.SubscriptionDefaultManager.target_number_is_outbound(
                        target_number=target_number
                ):
                    if channel:
                        channel.context = ChannelContext.OUTBOUND

                    caller_channel = channel or Channel(
                        raw_channel,
                        channel_flow=flow,
                        channel_context=ChannelContext.OUTBOUND,
                        target_number=target_number,
                        channel_intent=intent,
                        is_transferred=channel_is_transferred,
                    )

                    caller_channel.init_spy_iccs(spy_iccs)
                    caller_channel.init_spy_iris(spy_iris)
                    caller_channel.set_billing(billing_control)

                    caller_channel.call_id = call_id or DefaultCallManagerPool.issue_call_id(caller_channel)
                    target_number = CallControl.SubscriptionDefaultManager.outbound_number_regulation(target_number)
                    call.serve_outbound_call(
                        caller_channel,
                        target_number,
                        forwarder_extension=forwarder_extension,
                        forwarder_app=forwarder_app
                    )

                    return call
            # else:
            if channel:
                channel.context = ChannelContext.INTERNAL

            caller_channel = channel or Channel(
                raw_channel,
                channel_flow=flow,
                channel_context=ChannelContext.INTERNAL,
                target_number=target_number,
                channel_intent=intent
            )

            caller_channel.init_spy_iccs(spy_iccs)
            caller_channel.init_spy_iris(spy_iris)
            caller_channel.set_billing(billing_control)

            caller_channel.call_id = \
                call_id or DefaultCallManagerPool.issue_call_id(caller_channel)
            call.serve_internal_call(
                caller_channel,
                target_number,
                forwarder_extension=forwarder_extension,
                forwarder_app=forwarder_app
            )

            return call

        # There is no context for incoming channel...
        if raw_channel:
            raw_channel.hangup()
        if channel:
            channel.hangup()
