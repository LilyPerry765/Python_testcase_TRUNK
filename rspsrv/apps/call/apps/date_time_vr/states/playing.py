from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent, EndingCause
from rspsrv.apps.call.apps.date_time_vr.states.base import DateTimeVRStateName


class PlayingState(SimpleState):
    state_name = DateTimeVRStateName.PLAYING

    def __init__(self, machine, **kwargs):
        super(PlayingState, self).__init__(state_machine=machine, **kwargs)
        self.playback_is_finished = False
        self.playback_iterator = None

    def on_timeout(self):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Base.TIMEOUT, cause=EndingCause.APP_TIMEOUT)

    def on_playback_finished(self):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Playback.FINISHED, cause=EndingCause.PLAYBACK_FINISHED)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, cause=EndingCause.CALLER_HANGUP)

    def get_playback(self):
        try:
            return next(self.playback_iterator)
        except StopIteration:
            return None

    def play_playback(self, **kwargs):
        self.events.playback = self.get_playback()
        if self.events.playback is None:
            self.on_playback_finished()
            return
        self.events.playback.on_event(SimpleEvent.Application.FINISHED, self.play_playback)
        self.events.playback.enter()

    def enter(self, **kwargs):
        self.events.channel_hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                   self.on_channel_hangup)
        self.events.channel_destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                      self.on_channel_destroyed)

        if not isinstance(self.handlers.playbacks, list):
            self.cleanup()
            self.machine.change_state(SimpleEvent.Playback.FINISHED, cause=EndingCause.PLAYBACK_FINISHED)

        self.playback_iterator = iter(self.handlers.playbacks)

        self.play_playback()

    def __str__(self):
        return PlayingState.state_name
