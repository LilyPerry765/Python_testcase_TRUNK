import logging

from django.conf import settings
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
from rspsrv.apps.call.call_control.icc import ICCManager
from rspsrv.apps.call.call_control.spy import Interception

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
        self.machine.change_state(
            ExtensionEvent.Caller.DESTROYED,
            cause=EndingCause.CALLER_DESTROYED,
        )

    def on_caller_hangup(self, raw_channel, event):
        if self.machine.blinded:
            return

        print("Caller on conferencing destroyed.")

        self.machine.blinded = True
        self.cleanup()
        self.machine.change_state(
            ExtensionEvent.Caller.HANGUP,
            cause=EndingCause.CALLER_HANGUP,
        )

    def initialize_conference_icc(self, channel):
        if settings.LI_ENABLED:
            try:
                li_data = Interception.check_for_spy(
                    self.machine.subscription.number,
                )
            except Exception as e:
                logger.error(e)
                return

            if li_data:
                channel.li_data.extend(li_data)

                for d in li_data:
                    d.interception_mode = 'Combine'
                    icc = ICCManager(
                        target_channel=channel,
                        li_data=d,
                        active=True,
                        call_id=channel.call_id,
                    )
                    channel.spy_iccs.append(icc)

    def enter(self, **kwargs):
        self.target_number = kwargs.get('target_number', None)
        self.handlers.bridge.protected = True
        self.machine.next = None

        try:
            self.machine.channel.raw_channel.hold()
        except HTTPError:
            pass

        try:
            self.handlers.bridge.remove_channel(channel=self.machine.channel)
        except HTTPError:
            pass

        try:
            self.machine.channel.raw_channel.ring()
        except HTTPError:
            pass

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
