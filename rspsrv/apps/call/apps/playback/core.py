import uuid

from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent
from rspsrv.apps.call.apps.playback.states.base import PlaybackLogic
from rspsrv.apps.call.apps.playback.states.ending import EndingState
from rspsrv.apps.call.apps.playback.states.playing import PlayingState
from rspsrv.apps.call.apps.playback.states.setup import SetupState


class Playback(BaseCallApplication):
    app_name = "Playback"
    app_detail = "Plays a media on channel."

    def __init__(self, channel, media=None, number=None, digits=None, ordinal=None, target_number=0, next=None,
                 controls=False, cause="unknown", **kwargs):
        super(Playback, self).__init__(channel=channel, target_number=target_number)

        self.cause = cause
        self.next = next
        self.controls = controls

        if media:
            self.playback = media
            self.logic = PlaybackLogic.MEDIA
        elif number:
            self.playback = number
            self.logic = PlaybackLogic.NUMBER
        elif digits:
            self.playback = digits
            self.logic = PlaybackLogic.DIGITS
        else:
            raise BaseCallApplication.CallAppError("No logic (media, number, digits) is selected.")

        self.playback_id = uuid.uuid4()
        self.player = None

    def __setup_state_machine(self):
        self.app_states.setup = SetupState(self)
        self.app_states.playing = PlayingState(self)
        self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.setup
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.setup, SimpleEvent.Playback.STARTED, self.app_states.playing)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)

        self.add_transition(self.app_states.playing, SimpleEvent.Playback.FINISHED, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)

    def enter(self, **kwargs):
        super(Playback, self).enter()
        self.__setup_state_machine()
        self.start()

    @classmethod
    def get_name(cls):
        return cls.app_name

    @classmethod
    def get_detail(cls):
        return cls.app_detail

    def __str__(self):
        return Playback.app_name

    def terminate(self, **kwargs):
        if self.player is not None:
            try:
                self.player.stop()
            except:
                pass

        super(Playback, self).terminate(**kwargs)

    def close(self, force):
        self.terminate(force=force)


