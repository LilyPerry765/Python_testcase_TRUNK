from django.conf import settings
from rspsrv.apps.call.apps.playback.core import Playback
from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent, EndingCause, SimpleTimeout
from rspsrv.apps.call.apps.ext_dispatcher.states.base import ExtDispatcherStateName


class ReceivingState(SimpleState):
    state_name = ExtDispatcherStateName.RECEIVING

    def __init__(self, machine, **kwargs):
        super(ReceivingState, self).__init__(state_machine=machine, **kwargs)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, cause=EndingCause.CALLER_HANGUP)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_timeout(self):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Base.TIMEOUT, cause=EndingCause.APP_TIMEOUT)

    def on_dtmf_received(self, raw_channel, event):
        if self.events.playback:
            self.events.playback.terminate()
            self.events.playback = None
        digit = event.get('digit')
        if digit == SimpleEvent.DTMF.DTMF_STAR:
            if self.machine.target_extension:
                self.machine.next = (None, self.machine.target_extension)
            self.cleanup()
            self.machine.change_state(SimpleEvent.DTMF.DTMF_STAR, cause=EndingCause.APP_FINISHED)
        elif digit != SimpleEvent.DTMF.DTMF_OCTOTHORPE:
            self.machine.target_extension += digit

    def on_playback_finished(self, **kwargs):
        self.events.timeout = SimpleTimeout(self.machine.timeout, call_back=self.on_timeout)
        return

    def enter(self, **kwargs):
        self.events.channel_hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                   self.on_channel_hangup)
        self.events.channel_destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                      self.on_channel_destroyed)
        self.events.dtmf_received = self.machine.channel.on_event(SimpleEvent.Channel.DTMF_RECEIVED,
                                                                  self.on_dtmf_received)

        media = settings.DEFAULT_PLAYBACK['BEEP']
        self.events.playback = Playback(channel=self.machine.channel, media=media)
        self.events.playback_finished = self.events.playback.on_event(SimpleEvent.Application.FINISHED,
                                                                      self.on_playback_finished)
        self.events.playback.enter()

    def __str__(self):
        return self.state_name
