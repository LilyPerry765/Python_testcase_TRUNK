import datetime
from khayyam import JalaliDatetime

from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent
from rspsrv.apps.call.apps.date_time_vr.states.ending import EndingState
from rspsrv.apps.call.apps.date_time_vr.states.playing import PlayingState
from rspsrv.apps.call.apps.date_time_vr.states.setup import SetupState


class DateTimeVR(BaseCallApplication):
    app_name = "DateTime VR"
    app_details = "Plays Date and Time on repeat on channel"

    def __init__(self, caller_channel, dt=None, next=None, dt_str_format=None, **kwargs):
        super(DateTimeVR, self).__init__(channel=caller_channel, target_number=0)

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
        self.timeout = kwargs.get('timeout', 30)

    def __setup_state_machine(self):
        self.app_states.setup = SetupState(self)
        self.app_states.playing = PlayingState(self)
        self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.setup
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.setup, SimpleEvent.Playback.CHAINED, self.app_states.playing)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Base.TIMEOUT, self.app_states.ending)

        self.add_transition(self.app_states.playing, SimpleEvent.Playback.FINISHED, self.app_states.setup)
        self.add_transition(self.app_states.playing, SimpleEvent.Base.TIMEOUT, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)

    def enter(self, **kwargs):
        super(DateTimeVR, self).enter()
        self.__setup_state_machine()
        self.start()

    @classmethod
    def get_name(cls):
        return cls.app_name

    @classmethod
    def get_detail(cls):
        return cls.app_details

    def __str__(self):
        return DateTimeVR.app_name

    def close(self, force):
        self.terminate(force=force)
