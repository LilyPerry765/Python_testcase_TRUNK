import time

import requests
from django.conf import settings

from .bridge import Bridge, BridgeType
from .call_pool import LI
from .channel import ChannelFlow, Channel


class InterceptionMode(object):
    UNKNOWN, SPLIT, COMBINE = range(3)


class ICCManager(object):
    def __init__(self, target_channel, li_data, active=True, **kwargs):
        """

        :param target_channel:
         :type target_channel: CallManagerChannel
        :param li_data:
        :param active:
        """
        self.target_channel = target_channel
        self.call_id = kwargs.pop('call_id', 1)
        self._cin = LI.get_cin()
        self.timestamp = str(time.time())
        self.affected_channel = None

        self.li_data = li_data

        self.interception_mode_code = {"Split A": InterceptionMode.SPLIT,
                                       "Split B": InterceptionMode.SPLIT,
                                       "Combine": InterceptionMode.COMBINE
                                       }.get(li_data.interception_mode, InterceptionMode.UNKNOWN)

        if self.interception_mode_code == InterceptionMode.SPLIT:
            self.snoop_channels = {"IN": None, "OUT": None}
            self.spy_bridges = {"IN": None, "OUT": None}
            self.spy_channels = {"IN": None, "OUT": None}
        else:
            self.snoop_channels = {"BOTH": None}
            self.spy_bridges = {"BOTH": None}
            self.spy_channels = {"BOTH": None}

        self.activated = False
        if active:
            # print "Spying started!"
            self._start_init_chains()

    def _start_init_chains(self):
        self.activated = True
        self._init_bridges()

    def _init_bridges(self):
        for bridge_type in self.spy_bridges:
            if self.spy_bridges[bridge_type] is None:
                # init bridge...
                self.spy_bridges[bridge_type] = Bridge.create_bridge(bridge_type=BridgeType.MIXING,
                                                                     name="sb_%s_%s" % (
                                                                         bridge_type,
                                                                         self.target_channel.uid))

                print("bridges_created")
                self._init_snoop(bridge_type)

    def _init_snoop(self, snoop_type):
        if self.snoop_channels[snoop_type] is None:
            self.snoop_channels[snoop_type] = self.target_channel.get_spy(
                settings.SWITCHMANAGER_APP_NAME,
                spy=snoop_type.lower(),
                app_args="internal_snoop_in"
            )
            self.snoop_channels[snoop_type].raw_channel.on_event('StasisStart',
                                                                 lambda *args: self._add_channel_to_bridge(
                                                                     self.snoop_channels[snoop_type],
                                                                     self.spy_bridges[snoop_type]))
            print("snoops_created")
            self._init_spy(snoop_type)

    def _init_spy(self, spy_type):
        self.activated = True

        caller_id = ';'.join(
            [
                self.li_data.liid,
                self._cin,
                settings.OPERATOR_IDENTIFIER,
                '1',
                {
                    'IN': '1',
                    'OUT': '2',
                    'MIX': '3'
                }.get(spy_type, '0')
            ]
        )

        if self.spy_channels[spy_type] is None:
            self.spy_channels[spy_type] = Channel.create_channel(self.li_data.pri_voice_num, 'spy',
                                                                 flow=ChannelFlow.SPY,
                                                                 endpoint_context="@LI",
                                                                 caller_id=caller_id)
            self.spy_channels[spy_type].raw_channel.on_event('StasisStart',
                                                             lambda *args: self._add_channel_to_bridge(
                                                                 self.spy_channels[spy_type],
                                                                 self.spy_bridges[spy_type]))
            if self.li_data.on_fail_dialing == "true":
                self.spy_channels[spy_type].raw_channel.on_event('StasisEnd',
                                                                 lambda *args: self._end_original_call())
                self.spy_channels[spy_type].raw_channel.on_event('ChannelDestroyed',
                                                                 lambda *args: self._end_original_call())
            print("spy created")

    def _add_channel_to_bridge(self, channel, bridge):
        try:
            bridge.add_channel(channel=channel)
        except requests.HTTPError as e:
            print("\n\n", e, "\n\n")

            return False

        return True

    def _end_original_call(self):
        self.target_channel.hangup_channel()
        self.destroy()

    def change_target_channel(self, channel):
        self.target_channel = channel

        for snoop_type in self.snoop_channels:
            self.snoop_channels[snoop_type].kill_channel()
            self.snoop_channels[snoop_type] = self.target_channel.get_spy(
                settings.SWITCHMANAGER_APP_NAME,
                spy=snoop_type.lower(),
                app_args='internal_snoop_in'
            )
            self._add_channel_to_bridge(self.snoop_channels[snoop_type], self.spy_bridges[snoop_type])

    def destroy(self):
        for c in self.snoop_channels:
            if self.snoop_channels[c]:
                self.snoop_channels[c].kill_channel()
        for c in self.spy_channels:
            if self.spy_channels[c]:
                self.spy_channels[c].kill_channel()
        for b in self.spy_bridges:
            if self.spy_bridges[b]:
                self.spy_bridges[b].destroy()
        self.activated = False
