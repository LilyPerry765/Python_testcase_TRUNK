from rspsrv.apps.call.apps.base import SimpleState


class EndingState(SimpleState):
    state_name = "ending"

    def __init__(self, machine, **kwargs):
        super(EndingState, self).__init__(machine=machine, **kwargs)

    def enter(self, cause=None):
        print("Cause: %s" % cause)

        print("Next: ", self.machine.next)
        print("Machine history: ",
              ", ".join(map(lambda t: "%s-> %s" % (str(t[0]), str(t[1])), self.machine.history)))

        self.machine.end(cause=cause, next=self.machine.next)

