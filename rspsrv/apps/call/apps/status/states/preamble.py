from datetime import datetime
from django.conf import settings
from khayyam import JalaliDatetime

from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent, EndingCause, SimpleTimeout
from rspsrv.apps.call.apps.defaults.datetime_playback.core import DatetimePlayback
from rspsrv.apps.call.apps.playback.core import Playback
from rspsrv.apps.call.apps.status.states.base import ExtensionStatusStateName, ExtensionStatusCommand
from rspsrv.apps.extension.models import ExtensionStatus


class PreambleState(SimpleState):
    state_name = ExtensionStatusStateName.PREAMBLE

    def __init__(self, machine, **kwargs):
        super(PreambleState, self).__init__(machine=machine, **kwargs)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, cause=EndingCause.CALLER_HANGUP)

    def on_dtmf_received(self, raw_channel, event):
        dtmf = event.get('digit')

        command = {
            SimpleEvent.DTMF.DTMF_0: ExtensionStatusCommand.SET_DEFAULT,
            SimpleEvent.DTMF.DTMF_1: ExtensionStatusCommand.SET_AVAILABLE,
            SimpleEvent.DTMF.DTMF_2: ExtensionStatusCommand.SET_FORWARD,
            SimpleEvent.DTMF.DTMF_3: ExtensionStatusCommand.SET_DND,
            SimpleEvent.DTMF.DTMF_4: ExtensionStatusCommand.SET_DISABLE,
        }.get(dtmf, ExtensionStatusCommand.UNKNOWN)

        self.cleanup()
        self.machine.change_state(SimpleEvent.DTMF.DTMF_ANY, command=command)

    def on_timeout(self):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Timeout.GLOBAL, cause=EndingCause.APP_TIMEOUT)

    def enter(self, **kwargs):
        self.machine.channel.answer()

        self.events.channel_destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                      self.on_channel_destroyed)
        self.events.channel_hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                   self.on_channel_hangup)

        self.events.current_state_pre_playback = Playback(channel=self.machine.channel,
                                                          media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                          ['PRE_STATUS'])

        self.events.current_state_playback = Playback(channel=self.machine.channel,
                                                      media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                      [self.machine.extension_webapp.status.upper()])
        self.events.status_menu_playback = Playback(channel=self.machine.channel,
                                                    media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                    ['MENU'])

        self.events.current_state_pre_playback.enter()
        self.events.current_state_pre_playback.on_event(SimpleEvent.Application.FINISHED,
                                                        self.events.current_state_playback.enter)

        if self.machine.extension_webapp.status != ExtensionStatus.DISABLE:
            self.events.on_dtmf = self.machine.channel.on_event(SimpleEvent.Channel.DTMF_RECEIVED,
                                                                self.on_dtmf_received)
            self.events.timeout = SimpleTimeout(90, self.on_timeout)

            self.events.current_state_playback.on_event(SimpleEvent.Application.FINISHED,
                                                        self.events.status_menu_playback.enter)

        else:
            self.cleanup()
            self.machine.change_state(SimpleEvent.Base.TERMINATE, cause=EndingCause.APP_FINISHED)
