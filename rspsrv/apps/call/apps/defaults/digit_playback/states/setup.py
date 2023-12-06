from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent, EndingCause
from rspsrv.apps.call.apps.defaults.digit_playback.states.base import DigitPlaybackStateName


class SetupState(SimpleState):
    state_name = DigitPlaybackStateName.SETUP

    def __init__(self, machine, **kwargs):
        super(SetupState, self).__init__(state_machine=machine, **kwargs)

    def on_playbacks_chained(self):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Playback.CHAINED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, cause=EndingCause.CALLER_HANGUP)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def enter(self, **kwargs):
        self.events.channel_destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                      self.on_channel_destroyed)
        self.events.channel_hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                   self.on_channel_hangup)

