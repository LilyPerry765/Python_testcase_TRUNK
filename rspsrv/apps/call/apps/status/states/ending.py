from rspsrv.apps.call.apps.base import SimpleState
from rspsrv.apps.call.apps.status.states.base import ExtensionStatusStateName


class EndingState(SimpleState):
    state_name = ExtensionStatusStateName.ENDING

    def __init__(self, machine, **kwargs):
        super(EndingState, self).__init__(machine=machine, **kwargs)

    def enter(self, cause=None, **kwargs):
        self.machine.blinded = True
        print("Cause: %s" % cause)

        print("Next: ", self.machine.next)
        print("Machine history: ", ", ".join(map(lambda t: "%s-> %s" % (str(t[0]), str(t[1])), self.machine.history)))
        self.cleanup()

        params = {}

        self.machine.end(cause=cause, next=self.machine.next, **params)

    def __str__(self):
        return EndingState.state_name
