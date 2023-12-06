from rspsrv.apps.call.apps.base import SimpleState
from rspsrv.apps.call.apps.extension_call.states.base import ExtensionCallStateName


class HangUpState(SimpleState):
    state_name = ExtensionCallStateName.HANGUP

    def __init__(self, call):
        super(HangUpState).__init__(call)
        self.call = call

    def enter(self):
        pass

    def cleanup(self):
        pass

    def __str__(self):
        return HangUpState.state_name
