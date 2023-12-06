from rspsrv.apps.call.apps.base import Dynamics


class CallState(object):
    state_name = ""

    def __init__(self, change_state_callback, channel):
        self.change_state_callback = change_state_callback
        self.channel = channel
        self.events = Dynamics.Event()

    def enter(self, **kwargs):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def change_state(self, event, **kwargs):
        return self.change_state_callback(event, **kwargs)
