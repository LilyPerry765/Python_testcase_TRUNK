from rspsrv.apps.call.apps.base import SimpleState, EndingCause
from rspsrv.apps.call.apps.defaults.datetime_playback.states.base import DatetimePlaybackStateName


class EndingState(SimpleState):
    state_name = DatetimePlaybackStateName.ENDING

    def __init__(self, machine, **kwargs):
        super(EndingState, self).__init__(state_machine=machine, **kwargs)

    def enter(self, cause=EndingCause.APP_FINISHED, **kwargs):
        self.machine.player = None
        if not cause:
            cause = self.machine.cause

        print("Cause: %s" % cause)

        print("Next: ", self.machine.next)
        print("Machine history: ",
              ", ".join(map(lambda t: "%s-> %s" % (str(t[0]), str(t[1])), self.machine.history)))
        self.machine.end(cause=cause, next=self.machine.next)

