from rspsrv.apps.call.apps.base import BaseCallApplication
from rspsrv.apps.call.apps.base import SimpleEvent
from rspsrv.apps.call.apps.ext_dispatcher.states.receiving import ReceivingState
from rspsrv.apps.call.apps.ext_dispatcher.states.ending import EndingState


class ExtDispatcher(BaseCallApplication):
    app_name = "Extension Dispatcher"
    app_details = "Transfer the call from ivr to an extension."

    def __init__(self, caller_channel, **kwargs):
        super(ExtDispatcher, self).__init__(channel=caller_channel)
        self.next = None
        self.timeout = kwargs.get('timeout', 30)
        self.target_extension = ""

    def __setup_state_machine(self):
        self.app_states.receiving = ReceivingState(self)
        self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.receiving
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.receiving, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        self.add_transition(self.app_states.receiving, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.receiving, SimpleEvent.Base.TIMEOUT, self.app_states.ending)
        self.add_transition(self.app_states.receiving, SimpleEvent.DTMF.DTMF_STAR, self.app_states.ending)

    def enter(self):
        super(ExtDispatcher, self).enter()
        self.__setup_state_machine()
        self.start()

    def get_name(self):
        return ExtDispatcher.app_name

    def get_detail(self):
        return ExtDispatcher.app_details

    def __str__(self):
        return ExtDispatcher.app_name
