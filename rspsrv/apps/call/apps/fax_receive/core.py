from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent
# from rspsrv.apps.call.apps.fax_receive.states.ending import EndingState
from rspsrv.apps.call.apps.fax_receive.states.receiving import ReceivingState
from rspsrv.apps.call.apps.fax_receive.states.waiting import WaitingState


class FaxReceive(BaseCallApplication):
    app_name = 'Fax receiver'
    app_detail = 'Receiving incoming faxes'

    def __init__(self, caller_channel, target_number, call_id, next=None, **kwargs):
        super(FaxReceive, self).__init__(channel=caller_channel, target_number=target_number)

        self.next = next
        self.call_id = call_id
        self.cdr_id = None
        self.cdr = kwargs.get('cdr', None)
        if self.cdr_id is None and self.cdr is not None:
            self.cdr_id = self.cdr.id

    def __setup_state_machine(self):
        self.app_states.waiting = WaitingState(self)
        self.app_states.receiving = ReceivingState(self)
        # self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.waiting
        self.terminating_state = self.app_states.receiving

        self.add_transition(self.app_states.waiting, SimpleEvent.Playback.FINISHED, self.app_states.receiving)
        self.add_transition(self.app_states.waiting, SimpleEvent.Channel.DESTROYED, self.app_states.receiving)
        self.add_transition(self.app_states.waiting, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.receiving)
        # self.add_transition(self.app_states.waiting, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        # self.add_transition(self.app_states.waiting, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)

        # self.add_transition(self.app_states.receiving, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        # self.add_transition(self.app_states.receiving, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        # self.add_transition(self.app_states.receiving, SimpleEvent.Application.FINISHED, self.app_states.ending)

    def enter(self):
        super(FaxReceive, self).enter()
        self.__setup_state_machine()
        self.start()

    def get_name(self):
        return FaxReceive.app_name

    def get_detail(self):
        return FaxReceive.app_detail
