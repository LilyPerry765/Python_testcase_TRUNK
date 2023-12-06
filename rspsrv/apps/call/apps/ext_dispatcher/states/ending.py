from rspsrv.apps.call.apps.base import SimpleState
from rspsrv.apps.call.apps.ext_dispatcher.states.base import ExtDispatcherStateName


class EndingState(SimpleState):
    state_name = ExtDispatcherStateName.ENDING

    def __init__(self, machine, **kwargs):
        super(EndingState, self).__init__(state_machine=machine, **kwargs)

    def enter(self, cause=None, **kwargs):
        self.machine.blinded = True
        print("Next: ", self.machine.next)
        print("Machine history: ", ", ".join(map(lambda t: "%s-> %s" % (str(t[0]), str(t[1])), self.machine.history)))
        self.cleanup()
        self.machine.end(cause=cause, next=self.machine.next)

    def __str__(self):
        return self.state_name
