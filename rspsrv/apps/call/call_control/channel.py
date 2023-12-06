import logging
import re
import uuid
from threading import Timer

import requests
from django.conf import settings

from rspsrv.apps.call.apps.base import SimpleEvent, SimpleStateType
from rspsrv.apps.call.asn.asn_mod import IRIConstants
from rspsrv.apps.call.call_control.base import ARIDefaultManager
from rspsrv.apps.call.utils import timer_hangup

logger = logging.getLogger("call")


class ChannelFlow(object):
    INCOMING = 'incoming'
    OUTGOING = 'outgoing'
    REDIRECT = 'redirect'
    SNOOP = 'snoop'
    SPY = 'spy'


class ChannelContext:
    SYSTEM = 'system'
    INTERNAL = 'internal'
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'
    FEATURE = 'feature'
    UNKNOWN = 'unknown'


class ChannelIntent:
    CALL = 'call'
    TRANSFER = 'transfer'
    TRANSFERRING = 'transferring'
    CONFERENCE = 'conference'


class SpyChannelDirection(object):
    NONE = 'none'
    BOTH = 'both'
    OUTGOING = 'out'
    INCOMING = 'in'


SpyAudioDirection = SpyWhisperDirection = SpyChannelDirection


class Channel(object):
    def __init__(self, raw_channel, channel_flow, channel_context,
                 channel_intent=ChannelIntent.CALL, originator=None,
                 target_number=None, billing_control=None, **kwargs):
        self.events = []
        self.raw_channel = raw_channel
        self.originator = originator
        self.alive = True
        self.uid = raw_channel.id
        self.flow = channel_flow
        self.protected = False
        self.intent = channel_intent
        self.is_transferred = kwargs.pop('is_transferred', False)
        self.state = raw_channel.json.get('state')

        if channel_context == ChannelContext.INBOUND:
            self.extension_number = raw_channel.json['caller']['number']
        else:
            self.extension_number = \
            raw_channel.json['name'].split('-')[0].split('/')[1]

        self.mask_number = None

        self.destructor = None
        self.spying = False
        self.context = channel_context
        self.redirect_channel = None
        self.redirect_bridge = None
        self.conferenced_channel = None
        self.authenticated = False
        self.ongoing_call = None

        self.billing_control = billing_control

        self.li_data = kwargs.get('li_data', [])
        self.spy_iris = []
        self.spy_iccs = []
        self.keep_safe_spy_iccs = []

        self.on_hold_callback = kwargs.get('on_hold_callback', None)
        self.on_unhold_callback = kwargs.get('on_unhold_callback', None)

        if originator is not None:
            self.call_id = originator.call_id
        else:
            self.call_id = None

        if self.flow == ChannelFlow.INCOMING or self.flow == \
                ChannelFlow.REDIRECT:
            self.endpoint_number = self.extension_number
            self.source_number = self.endpoint_number
            self.destination_number = target_number
            self.caller_id = raw_channel.json['caller']['name']

        elif self.flow == ChannelFlow.OUTGOING:
            self.source_number = self.originator.source_number
            self.caller_id = self.originator.caller_id
            self.endpoint_number = self.extension_number
            self.destination_number = self.originator.destination_number

        # ?? dafuq?
        if self.intent != ChannelFlow.SNOOP:
            self.events.append(
                self.raw_channel.on_event(SimpleEvent.Channel.STATE_CHANGE,
                                          self.update_state))
            self.events.append(
                self.raw_channel.on_event(SimpleEvent.Channel.UNHOLD,
                                          self.on_unhold))
            self.events.append(
                self.raw_channel.on_event(SimpleEvent.Channel.HOLD,
                                          self.on_hold))
            self.events.append(
                self.raw_channel.on_event(SimpleEvent.Channel.DESTROYED,
                                          self.destroyed))
            self.events.append(
                self.raw_channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                          self.hungup))

    def send_packet(self, packet_type, affected_number=None, supps_type=None,
                    end_cause=None, two_legs_only=False,
                    all_legs=True):
        targeted_iris = self.spy_iris
        if affected_number:
            targeted_iris = [iri for iri in self.spy_iris if
                             iri.affected_number == affected_number]

        if packet_type == IRIConstants.Record.BEGIN:
            for iri in targeted_iris:
                iri.set_record_begin(supps_type=supps_type)
            return

        if packet_type == IRIConstants.Record.CONTINUE:
            for iri in targeted_iris:
                iri.set_record_continue(supps_type=supps_type)
            return

        if packet_type == IRIConstants.Record.REPORT:
            if supps_type:
                if supps_type[
                    'service_action'] == \
                        IRIConstants.SERVICE_ACTION.ACTIVATION:
                    for iri in targeted_iris:
                        iri.set_supps_act_record_report(supps_type=supps_type)
                elif supps_type[
                    'service_action'] == \
                        IRIConstants.SERVICE_ACTION.DEACTIVATION:
                    for iri in targeted_iris:
                        iri.set_supps_deact_record_report(
                            supps_type=supps_type)
                return
            for iri in targeted_iris:
                iri.set_record_report()
            return

        if packet_type == IRIConstants.Record.END:
            for iri in targeted_iris:
                iri.set_record_end(end_cause=end_cause,
                                   two_legs_only=two_legs_only,
                                   all_legs=all_legs)
            return

    def set_state(self, state_name, affected_number=None):
        targeted_iris = self.spy_iris
        if affected_number:
            targeted_iris = [iri for iri in self.spy_iris if
                             iri.affected_number == affected_number]

        if state_name == IRIConstants.State.SETUP:
            for iri in targeted_iris:
                iri.set_state_setup()
            return
        if state_name == IRIConstants.State.CONNECTED:
            for iri in targeted_iris:
                iri.set_state_connected()
            return

        if state_name == IRIConstants.State.IDLE:
            for iri in targeted_iris:
                iri.set_state_idle()
            return

    def re_active_iris(self):
        for iri in self.spy_iris:
            iri.re_active()

    def remove_affected_number_iris(self, affected_number):
        self.spy_iris = [iri for iri in self.spy_iris if
                         iri.affected_number != affected_number]

    def change_affected_number_iris(self, affected_number):
        for iri in self.spy_iris:
            iri.affected_number = affected_number

    def set_forwarded_to_party(self, forwarded_party_number):
        for iri in self.spy_iris:
            iri.set_forwarded_to_party(
                forwarded_party_number=forwarded_party_number)
        return

    def set_conferenced_to_party(self, conferenced_party_number,
                                 affected_number=None):
        if affected_number:
            affected_iris = [iri for iri in self.spy_iris if
                             iri.affected_number == affected_number]
        else:
            affected_iris = self.spy_iris

        for iri in affected_iris:
            iri.set_conferenced_to_party(
                conferenced_party_number=conferenced_party_number
            )
        return

    def set_self_destructor(self, timeout):
        pass

    def cancel_self_destructor(self):
        pass

    def update_state(self, *args):
        if len(args) < 2:
            return
        event = args[1]

        state = event['channel'].get('state', None)
        if state is None:
            return

        if state == SimpleStateType.Channel.UP:
            self.__start_billing()

        self.state = state

    def on_unhold(self, raw_channel, event, affected_number=None):
        if self.originator:
            affected_iris = self.originator.spy_iris
            if affected_number:
                affected_iris = [iri for iri in self.originator.spy_iris if
                                 iri.affected_number == affected_number]

            for iri in affected_iris:
                iri.set_record_continue(supps_type={
                    'service_action': IRIConstants.SERVICE_ACTION.TERMINATING,
                    'type': IRIConstants.SUPPLEMENTARY_SERVICE.HOLD,
                    'party_number': self.source_number,
                }, )

        affected_iris = self.spy_iris
        if affected_number:
            affected_iris = [iri for iri in self.spy_iris if
                             iri.affected_number == affected_number]

        for iri in affected_iris:
            iri.set_record_continue(supps_type={
                'service_action': IRIConstants.SERVICE_ACTION.TERMINATING,
                'type': IRIConstants.SUPPLEMENTARY_SERVICE.HOLD,
                'party_number': self.endpoint_number,
            }
            )

    def on_hold(self, raw_channel, event, affected_number=None):
        if self.originator:
            affected_iris = self.originator.spy_iris
            if affected_number:
                affected_iris = [iri for iri in self.originator.spy_iris if
                                 iri.affected_number == affected_number]

            for iri in affected_iris:
                iri.set_record_continue(
                    supps_type={
                        'service_action': IRIConstants.SERVICE_ACTION.USING,
                        'type': IRIConstants.SUPPLEMENTARY_SERVICE.HOLD,
                        'party_number': self.source_number,
                    }
                )

        affected_iris = self.spy_iris
        if affected_number:
            affected_iris = [iri for iri in self.spy_iris if
                             iri.affected_number == affected_number]

        for iri in affected_iris:
            iri.set_record_continue(supps_type={
                'service_action': IRIConstants.SERVICE_ACTION.USING,
                'type': IRIConstants.SUPPLEMENTARY_SERVICE.HOLD,
                'party_number': self.endpoint_number,
            },
            )

    def destroyed(self, raw_channel, event):
        if self.redirect_channel:
            return

        self.alive = False

        if hasattr(self.originator, 'redirect_bridge'):
            if self.originator.redirect_bridge:
                for iri in self.originator.spy_iris:
                    if iri.affected_channel == self:
                        iri.set_record_end()

        if self.originator and self.originator.intent == \
                ChannelIntent.TRANSFER:
            for iri in self.originator.spy_iris:
                if iri.affected_channel == self:
                    iri.set_record_end()

        for iri in self.spy_iris:
            iri.set_record_end()

        if not self.is_transferred:
            for icc in self.spy_iccs:
                for spy_channel in icc.spy_channels:
                    icc.spy_channels[spy_channel].hangup()

        if self.originator:
            for icc in self.originator.spy_iccs:
                if icc.affected_channel == self:
                    for spy_channel in icc.spy_channels:
                        icc.spy_channels[spy_channel].hangup()

    def hungup(self, raw_channel, event):
        if self.redirect_channel or self.intent == ChannelIntent.TRANSFER:
            return

        self.alive = False

    def close(self, force=False):
        if force or not self.protected:
            self.kill_channel()

    def hangup_channel(self):
        self.kill_channel()

    def answer(self):
        self.raw_channel.answer()
        Timer(
            settings.MAX_CALL_DURATION_SECONDS,
            timer_hangup,
            [self.raw_channel],
        ).start()

    def hangup(self, **kwargs):
        if self.protected:
            self.protected = False
            return
        if self.alive:
            try:
                self.raw_channel.hangup(**kwargs)
            except requests.HTTPError:
                return
            self.alive = False

    def play_with_id(self, **kwargs):
        return self.raw_channel.playWithId(**kwargs)

    def on_event(self, event, callback, **kwargs):
        event_handler = self.raw_channel.on_event(event, callback, **kwargs)
        self.events.append(event_handler)
        return event_handler

    def ring(self):
        self.raw_channel.ring()

    def kill_channel(self):
        if self.protected:
            self.protected = False
            return
        if self.alive:
            try:
                self.raw_channel.hangup()
            except requests.HTTPError:
                return
            self.alive = False

    def get_spy(self, app, spy=SpyAudioDirection.BOTH,
                whisper=SpyWhisperDirection.NONE, app_args=''):
        """

            spy: string - Direction of audio to spy on
                Default: none
                Allowed values: none, both, out, in
            whisper: string - Direction of audio to whisper into
                Default: none
                Allowed values: none, both, out, in
            app: string - (required) Application the snooping channel is
            placed into
            appArgs: string - The application arguments to pass to the
            Stasis application
            snoopId: string - Unique ID to assign to snooping channel

        :return:
        """
        try:
            snoop_raw_channel = self.raw_channel.snoopChannel(spy=spy,
                                                              whisper=whisper,
                                                              app=app,
                                                              appArgs=app_args)
        except requests.HTTPError:
            return None

        return Channel(snoop_raw_channel, channel_flow=ChannelFlow.SNOOP,
                       channel_context=ChannelContext.SYSTEM,
                       channel_intent=ChannelIntent.CALL)

    def __start_billing(self):
        if self.billing_control:
            self.billing_control.start()

    def stop_billing(self):
        if self.billing_control:
            self.billing_control.end()

    def set_billing(self, billing_control):
        self.billing_control = billing_control

    def events_unsubscriber(self):
        for event in self.events:
            try:
                event.close()
            except Exception as e:
                logger.error(e)

    @staticmethod
    def create_channel(endpoint_number, app_args,
                       originator=None,
                       endpoint_context=settings.ENDPOINT_CONTEXT,
                       flow=ChannelFlow.OUTGOING,
                       channel_context=ChannelContext.INTERNAL,
                       channel_intent=ChannelIntent.CALL,
                       caller_id=None,
                       channel_id=None,
                       billing_control=None,
                       forwarded=None,
                       **kwargs):
        is_local = kwargs.pop('is_local', False)
        endpoint_number = str(endpoint_number)

        if caller_id is None:
            caller_id = endpoint_number

        if channel_id is None:
            channel_id = str(uuid.uuid4().hex)

        if endpoint_number[0] != '/':
            endpoint_number = '/' + endpoint_number

        x_header = kwargs.pop('x_header', None)
        timeout = kwargs.get('timeout', -1)
        params = {
            'endpoint': settings.CONTROL_TECHNOLOGY + endpoint_number +
                        endpoint_context,
            'app': settings.SWITCHMANAGER_APP_NAME,
            'channelId': channel_id,
            'callerId': caller_id,
            'appArgs': app_args,
            'timeout': timeout
        }

        if originator:
            params['originator'] = originator.uid

        params['variables'] = {
            "SIPADDHEADER01": "NX-FromSw: True",
        }
        if channel_context == ChannelContext.OUTBOUND:
            params['variables'].update({
                "SIPADDHEADER02": "NX-Outbound: True",
            })
        if forwarded:
            params['variables'].update({
                "SIPADDHEADER03": "NX-Forwarded: True",
            })
        if is_local:
            params['variables'].update({
                "SIPADDHEADER04": "X-{0}: {1}".format('ISLOCAL', is_local)
            })
        if x_header:
            params['variables'].update({
                "SIPADDHEADER05": "X-{0}: {1}".format(
                    x_header['header_name'],
                    x_header['header_value'],
                )
            })

        try:
            outgoing = ARIDefaultManager.client.channels.originate(**params)
            channel = Channel(
                raw_channel=outgoing,
                channel_flow=flow,
                originator=originator,
                channel_context=channel_context,
                channel_intent=channel_intent,
                billing_control=billing_control
            )

            return channel
        except requests.HTTPError:
            return None

    def init_spy_iccs(self, spy_iccs):
        self.spy_iccs = spy_iccs

        for icc in self.spy_iccs:
            icc.change_target_channel(self)

    def init_spy_iris(self, spy_iris):
        self.spy_iris = spy_iris

        for iri in self.spy_iris:
            iri.change_target_channel(self)

    def move_spy_iccs(self, target_channel):
        for icc in self.spy_iccs:
            icc.change_target_channel(target_channel)

        target_channel.spy_iccs = self.spy_iccs
        self.spy_iccs = []

    def move_spy_iris(self, target_channel):
        for iri in self.spy_iris:
            iri.change_target_channel(target_channel)

        target_channel.spy_iris = self.spy_iris
        self.spy_iris = []

    def is_endpoint_internal(self):
        if self.endpoint_number == 'LB':
            return False
        return True

    # noinspection PyBroadException
    def get_variable(self, variable):
        try:
            get_value = self.raw_channel.getChannelVar(variable=variable)
        except Exception:
            return None
        if get_value and 'value' in get_value:
            value = get_value['value'].strip()
            return value
        return None

    # noinspection PyBroadException
    def get_endpoint_details(self):
        try:
            sip_header_value = self.raw_channel.getChannelVar(
                variable='ENDPOINT')
        except Exception:
            return None, None
        if 'value' in sip_header_value:
            x_endpoint = sip_header_value['value'].split(':')
            endpoint_type = x_endpoint[0].strip()
            endpoint_name = x_endpoint[1].strip() if len(
                x_endpoint) > 1 else None
            return endpoint_type, endpoint_name
        return None, None

    def set_mask_number(self, mask_sip_url):
        if mask_sip_url:
            pattern = r"<sip:\+?([0-9]+)@.+>"
            mask_number = re.search(pattern, mask_sip_url).group(1)
            self.mask_number = mask_number


class IORawChannel(object):
    def __init__(self, flow, context, trunk_name=None, target_number=None):
        self.flow = flow
        self.context = context
        self.trunk = trunk_name
        self.target_number = target_number

    def set_context(self, context):
        self.context = context

    def set_context_inbound(self):
        self.set_context(ChannelContext.INBOUND)
