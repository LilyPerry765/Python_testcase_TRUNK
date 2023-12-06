import datetime
from khayyam import JalaliDatetime

from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent
from rspsrv.apps.call.apps.defaults.datetime_playback.states.ending import EndingState
from rspsrv.apps.call.apps.defaults.datetime_playback.states.playing import PlayingState
from rspsrv.apps.call.apps.defaults.datetime_playback.states.setup import SetupState


class DatetimePlayback(BaseCallApplication):
    app_name = "Datetime Playback"
    app_details = "Plays Datetime on channel"

    def __init__(self, channel, dt=None, next=None, dt_str_format=None, **kwargs):
        super(DatetimePlayback, self).__init__(channel=channel, target_number=0)

        self.next = next

        if type(dt) is datetime.datetime:
            dt = JalaliDatetime(dt)

        elif type(dt) is str:
            if dt_str_format is None:
                raise BaseCallApplication.CallAppError('dt_str_format can not be None')
            else:
                try:
                    dt = datetime.datetime.strptime(dt, dt_str_format)
                except ValueError:
                    raise
        elif dt is None:
            dt = JalaliDatetime.now()
        else:
            raise BaseCallApplication.CallAppError('dt format is not correct: %s' % type(dt))

        self.datetime = dt

    def __setup_state_machine(self):
        self.app_states.setup = SetupState(self)
        self.app_states.playing = PlayingState(self)
        self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.setup
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.setup, SimpleEvent.Playback.CHAINED, self.app_states.playing)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)

        self.add_transition(self.app_states.playing, SimpleEvent.Playback.FINISHED, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)

    def enter(self, **kwargs):
        super(DatetimePlayback, self).enter()
        self.__setup_state_machine()
        self.start()

    @classmethod
    def get_name(cls):
        return cls.app_name

    @classmethod
    def get_detail(cls):
        return cls.app_details

    def __str__(self):
        return DatetimePlayback.app_name

    def close(self, force):
        # if 'playbacks' is self.handlers.__slots__:
        #     self.handlers.playbacks = list()
        self.terminate(force=force)
