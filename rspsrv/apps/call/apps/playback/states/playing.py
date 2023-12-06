from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent, EndingCause
from rspsrv.apps.call.apps.playback.states.base import PlaybackStateName


class PlayingState(SimpleState):
    state_name = PlaybackStateName.PLAYING

    def __init__(self, machine, **kwargs):
        super(PlayingState, self).__init__(state_machine=machine, **kwargs)

    def on_playback_finished(self, raw_playback, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Playback.FINISHED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, cause=EndingCause.CHANNEL_HANGUP)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, cause=EndingCause.CHANNEL_DESTROYED)

    def on_dtmf_received(self, raw_channel, event):
        pass

    def enter(self, **kwargs):
        self.events.playback_finished = self.machine.player.on_event(SimpleEvent.Playback.FINISHED,
                                                                     self.on_playback_finished)
        self.events.hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                           self.on_channel_hangup)
        self.events.destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                              self.on_channel_destroyed)

        if self.machine.controls:
            self.events.dtmf_received = self.machine.channel.on_event(SimpleEvent.Channel.DTMF_RECEIVED,
                                                                      self.on_dtmf_received)
