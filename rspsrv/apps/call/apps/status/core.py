from rspsrv.apps.call.apps.base import BaseCallApplication, SimpleEvent
from rspsrv.apps.call.apps.status.states.ending import EndingState
from rspsrv.apps.call.apps.status.states.preamble import PreambleState
from rspsrv.apps.call.apps.status.states.set_status import SetStatusState
from rspsrv.apps.extension.models import Extension


class ExtensionStatus(BaseCallApplication):
    app_name = "Extension Status"
    app_detail = "Handles extension's status setting"

    def __init__(self, caller_channel, target_number, next=None, **kwargs):
        super(ExtensionStatus, self).__init__(channel=caller_channel, target_number=target_number, **kwargs)

        self.next = next

        try:
            self.extension_webapp = Extension.objects.get(
                extension_number__number=caller_channel.extension_number)
        except (Extension.DoesNotExist, Extension.MultipleObjectsReturned):
            raise BaseCallApplication.WebAppNotExists

    def __setup_state_machine(self):
        self.app_states.preamble = PreambleState(self)
        self.app_states.set_status = SetStatusState(self)
        self.app_states.ending = EndingState(self)

        self.initial_state = self.app_states.preamble
        self.terminating_state = self.app_states.ending

        self.add_transition(self.app_states.preamble, SimpleEvent.DTMF.DTMF_ANY, self.app_states.set_status)
        self.add_transition(self.app_states.preamble, SimpleEvent.Base.TERMINATE, self.app_states.set_status)
        self.add_transition(self.app_states.preamble, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.preamble, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        self.add_transition(self.app_states.preamble, SimpleEvent.Timeout.GLOBAL, self.app_states.ending)

        self.add_transition(self.app_states.set_status, SimpleEvent.Channel.DESTROYED, self.app_states.ending)
        self.add_transition(self.app_states.set_status, SimpleEvent.Channel.HANGUP_REQUEST, self.app_states.ending)
        self.add_transition(self.app_states.set_status, SimpleEvent.Base.TERMINATE, self.app_states.ending)
        self.add_transition(self.app_states.set_status, SimpleEvent.Timeout.GLOBAL, self.app_states.ending)

    def enter(self):
        super(ExtensionStatus, self).enter()
        self.__setup_state_machine()
        self.start()

    def get_name(self):
        return ExtensionStatus.app_name

    def get_detail(self):
        return ExtensionStatus.app_detail
