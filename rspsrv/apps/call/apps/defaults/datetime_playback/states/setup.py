import datetime

from django.conf import settings
from khayyam import JalaliDatetime

from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent
from rspsrv.apps.call.apps.defaults.datetime_playback.states.base import DatetimePlaybackStateName
from rspsrv.apps.call.apps.playback.core import Playback


class SetupState(SimpleState):
    state_name = DatetimePlaybackStateName.SETUP

    def __init__(self, machine, **kwargs):
        super(SetupState, self).__init__(state_machine=machine, **kwargs)

    def on_playbacks_chained(self):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Playback.CHAINED)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST)

    def enter(self, **kwargs):
        self.events.channel_destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                      self.on_channel_destroyed)
        self.events.channel_hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                   self.on_channel_hangup)

        now = JalaliDatetime.now()

        self.handlers.playbacks = list()

        if self.machine.datetime.year != now.year:
            print("Playing year")
            self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                    media=str(self.machine.datetime.year)))

        if self.machine.datetime.date() < now.date():
            self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                    media=settings.DEFAULT_PLAYBACK['ORDINALS_PATH'] +
                                                    str(self.machine.datetime.day)))
            self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                    media=settings.DEFAULT_PLAYBACK['MONTHS_PATH'] +
                                                    str(self.machine.datetime.month)))

        self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                media=settings.DEFAULT_PLAYBACK['HOUR_']))

        self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                media=settings.DEFAULT_PLAYBACK['ORDINALS_PATH'] +
                                                str(self.machine.datetime.hour)))

        self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                media=settings.DEFAULT_PLAYBACK['ORDINALS_PATH'] +
                                                str(self.machine.datetime.minute)))

        self.handlers.playbacks.append(Playback(channel=self.machine.channel,
                                                media=settings.DEFAULT_PLAYBACK['MINUTE']))

        self.machine.change_state(SimpleEvent.Playback.CHAINED)
