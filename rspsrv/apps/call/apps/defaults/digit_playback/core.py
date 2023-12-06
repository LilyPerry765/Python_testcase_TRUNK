from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent


class DigitPlayback(BaseCallApplication):
    app_name = "Digit Playback"
    app_details = "Plays digits on channel"

    def __init__(self, channel, target_number=0, digits=None, next=next, **kwargs):
        super(DigitPlayback, self).__init__(channel=channel, target_number=target_number)

        self.next = next

        if type(digits) is int or type(digits) is str:
            self.digits = str(digits)
        else:
            raise BaseCallApplication.CallAppError("Digits type is not correct: %s" % type(digits))

    def __setup_stat_machine(self):
        self.app_states.setup = SetupState(self)
        self.app_states.playing = PlayingState(self)
        self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.setup
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.setup, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.setup, SimpleEvent.Playback.CHAINED, self.app_states.playing)

        self.add_transition(self.app_states.playing, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.playing, SimpleEvent.Playback.FINISHED, self.app_states.ending)

    def enter(self, **kwargs):
        super(DigitPlayback, self).enter()
        self.__setup_stat_machine()
        self.start()

    @classmethod
    def get_name(cls):
        return cls.app_name

    @classmethod
    def get_detail(cls):
        return cls.app_details

    def __str__(self):
        return "%s - %s" % (DigitPlayback.app_name, DigitPlayback.app_details)

