import logging

from requests.exceptions import HTTPError

from rspsrv.apps.call.apps.base import (
    SimpleEvent,
    SimpleState,
    EndingCause,
)
from rspsrv.apps.call.apps.extension_call.events import ExtensionEvent
from rspsrv.apps.call.apps.extension_call.states.base import (
    ExtensionCallStateName
)

logger = logging.getLogger("call")


class ConferencingState(SimpleState):
    state_name = ExtensionCallStateName.CONFERENCING

    def __init__(self, state_machine, **kwargs):
        super(ConferencingState, self).__init__(state_machine=state_machine, **kwargs)

        self.target_number = None

    def on_caller_destroyed(self, raw_channel, event):
        if self.machine.blinded:
            return

        self.machine.blinded = True

        print("Caller on conferencing destroyed.")
        self.cleanup()
        self.machine.change_state(ExtensionEvent.Caller.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_caller_hangup(self, raw_channel, event):
        if self.machine.blinded:
            return

        print("Caller on conferencing destroyed.")

        self.machine.blinded = True
        self.cleanup()
        self.machine.change_state(ExtensionEvent.Caller.HANGUP, cause=EndingCause.CALLER_HANGUP)

    def enter(self, **kwargs):
        self.target_number = kwargs.get('target_number', None)

        self.handlers.bridge.protected = True

        self.machine.next = None

        try:
            self.machine.channel.raw_channel.hold()
        except HTTPError as e:
            logger.error(e)

        try:
            self.handlers.bridge.remove_channel(channel=self.machine.channel)
        except HTTPError as e:
            logger.error(e)

        self.machine.channel.raw_channel.ring()

        self.events.caller_destroyed = self.machine.channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_caller_destroyed
        )
        self.events.caller_hangup = self.machine.channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_caller_hangup
        )

    def __str__(self):
        return ConferencingState.state_name
