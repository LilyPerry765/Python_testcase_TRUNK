import time
from threading import Timer

from django.conf import settings

from rspsrv.apps.call.apps.base import (
    SimpleEvent,
    EndingCause,
    SimpleState,
    SimpleTimeout,
)
from rspsrv.apps.call.apps.external_call.events import ExternalCallEvent
from rspsrv.apps.call.apps.external_call.states.base import (
    ExternalCallStateName
)
from rspsrv.apps.call.utils import timer_hangup


class RingingState(SimpleState):
    state_name = ExternalCallStateName.RINGING

    def __init__(self, machine, **kwargs):
        super(RingingState, self).__init__(machine=machine, **kwargs)

    def on_callee_hungup(self, raw_channel, event):
        print("CALLEE HUNGUP")
        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.HANGUP, cause=EndingCause.CALLEE_HANGUP)

    def on_caller_hungup(self, raw_channel, event):
        print("CALLER HANGUP")
        self.cleanup()
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(ExternalCallEvent.Caller.HANGUP, cause=EndingCause.CALLER_HANGUP)

    def on_callee_destroyed(self, raw_channel, event):
        print("CALLEE DESTROYED")
        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.DESTROYED, cause=EndingCause.CALLEE_DESTROYED,
                                  cause_code=event['cause'])

    def on_caller_destroyed(self, raw_channel, event):
        print("CALLER DESTROYED")
        self.cleanup()
        self.machine.next = None
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(ExternalCallEvent.Caller.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_talking_start(self, raw_channel, event):
        if event['channel']['state'] == SimpleEvent.Channel.UP:
            print(event['channel']['state'])
            print("TALKING STARTED")
            self.machine.channel.raw_channel.answer()
            Timer(
                settings.MAX_CALL_DURATION_SECONDS,
                timer_hangup,
                [self.machine.channel.raw_channel],
            ).start()
            self.cleanup()
            self.machine.change_state(SimpleEvent.Channel.TALKING_STARTED)

    def on_no_answer(self):  # timeout
        print("CALLEE NO ANSWER")
        self.cleanup()
        self.machine.change_state(ExternalCallEvent.Callee.NO_ANSWER, cause=EndingCause.CALLEE_NOANSWER)

    def enter(self):
        self.machine.ringing_time = time.time()

        self.events.callee_destroyed = self.machine.callee_channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_callee_destroyed
        )

        self.events.caller_destroyed = self.machine.channel.on_event(
            SimpleEvent.Channel.DESTROYED,
            self.on_caller_destroyed
        )

        self.events.callee_hangup = self.machine.callee_channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_callee_hungup
        )

        self.events.caller_hangup = self.machine.channel.on_event(
            SimpleEvent.Channel.HANGUP_REQUEST,
            self.on_caller_hungup
        )

        if self.machine.ring_max_seconds:
            self.events.timeout = SimpleTimeout(
                interval=self.machine.ring_max_seconds,
                call_back=self.on_no_answer
            )

        self.events.callee_answer = \
            self.machine.callee_channel.raw_channel.on_event(
                SimpleEvent.Channel.STATE_CHANGE,
                self.on_talking_start
            )

    def __str__(self):
        return RingingState.state_name
