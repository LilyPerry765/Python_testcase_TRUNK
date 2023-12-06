from rspsrv.apps.call.apps.base import SimpleEvent, SimpleState, EndingCause
from rspsrv.apps.call.apps.external_call.events import ExternalCallEvent
from rspsrv.apps.call.apps.external_call.states.base import ExternalCallStateName


class TransferringState(SimpleState):
    state_name = ExternalCallStateName.TRANSFERRING

    def __init__(self, state_machine, **kwargs):
        super(TransferringState, self).__init__(state_machine=state_machine, **kwargs)
        self.dtmf_string = ""
        self.transferor = None
        self.transferee = None
        self.target_number = None
        self.owner = None

    def on_transferee_destroyed(self, raw_channel, event):
        print("TRANSFEREE DESTROYED")

        if self.machine.blinded:
            return

        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.ATRANSFERRED, cause=EndingCause.CALLEE_ATRANSFERRED)

    def on_transferee_hungup(self, raw_channel, event):
        print("TRANSFEREE HUNGUP")

        if self.machine.blinded:
            return

        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.ATRANSFERRED, cause=EndingCause.CALLEE_ATRANSFERRED)

    def on_transferor_destroyed(self, raw_channel, event):
        print("TRANSFEROR DESTROYED")

        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.ATRANSFERRED, cause=EndingCause.CALLEE_ATRANSFERRED)

    def on_transferor_hungup(self, raw_channel, event):
        print("TRANSFEROR HANGUP")

        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.ATRANSFERRED, cause=EndingCause.CALLEE_ATRANSFERRED)

    def on_transferor_dtmf_received(self, raw_channel, event):
        if self.machine.blinded:
            return

        digit = event.get('digit')

        if digit == SimpleEvent.DTMF.DTMF_OCTOTHORPE:
            self.transferor.redirect_channel = None
            self.handlers.bridge.add_channel(channel=self.transferor)

            event = ExternalCallEvent.Caller.ATRANSFERRING_CANCELED
            self.handlers.bridge.add_channel(channel=self.machine.channel)

            self.cleanup()
            self.machine.change_state(event, redirect_channel=False)

        if digit == SimpleEvent.DTMF.DTMF_STAR:
            self.transferor.hangup()

    def enter(self, target_number, transferor, transferee, owner):
        self.machine.next = None
        self.transferor = transferor
        self.transferee = transferee
        self.target_number = target_number
        self.owner = owner

        self.transferee.raw_channel.hold()

        self.handlers.bridge.remove_channel(channel=self.transferor)

        self.transferor.raw_channel.ring()

        self.events.transferee_destroyed = self.transferee.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_transferee_destroyed
        )

        self.events.transferee_hungup = self.transferee.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_transferee_hungup
        )

        self.events.transferor_destroyed = self.transferor.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_transferor_destroyed
        )

        self.events.transferor_hungup = self.transferor.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_transferor_hungup
        )

        self.events.transferor_dtmf_received = self.transferor.on_event(
            SimpleEvent.Channel.DTMF_RECEIVED,
            self.on_transferor_dtmf_received
        )

    def __str__(self):
        return TransferringState.state_name
