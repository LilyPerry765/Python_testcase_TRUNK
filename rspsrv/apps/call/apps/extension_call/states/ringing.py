import logging
import time
from threading import Timer

from django.conf import settings

from rspsrv.apps.call.apps.base import (
    SimpleEvent,
    EndingCause,
    SimpleState,
    SimpleTimeout,
    SimpleStateType,
    CallApplicationType,
)
from rspsrv.apps.call.apps.extension_call.events import ExtensionEvent
from rspsrv.apps.call.apps.extension_call.states.base import (
    ExtensionCallStateName
)
from rspsrv.apps.call.utils import timer_hangup

logger = logging.getLogger("call")


class RingingState(SimpleState):
    state_name = ExtensionCallStateName.RINGING

    def __init__(self, machine, **kwargs):
        print("RINGING STATE")
        super(RingingState, self).__init__(machine=machine, **kwargs)
        self.redirected = False

    def on_callee_hungup(self, raw_channel, event):
        print("CALLEE HUNGUP")
        if self.machine.channel.redirect_channel:
            cause = EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
        else:
            cause = EndingCause.CALLEE_DESTROYED
        self.cleanup()
        self.machine.change_state(ExtensionEvent.Callee.HANGUP, cause=cause)

    def on_caller_hungup(self, raw_channel, event):
        print("CALLER HANGUP")
        if self.redirected:
            self.redirected = False
            return
        if self.machine.channel.redirect_channel:
            if self.machine.channel.redirect_channel.alive and not self.redirected:
                try:
                    self.events.caller_hungup.close()
                except Exception as e:
                    logger.error(e)
                self.redirected = True
                self.machine.channel.redirect_channel.raw_channel.unhold()
                self.handlers.bridge.add_channel(channel=self.machine.channel.redirect_channel)
                self.change_caller_channel(channel=self.machine.channel.redirect_channel)
                return
        self.cleanup()
        self.machine.next = None
        self.machine.final_state = event.get('cause_text')
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.change_state(ExtensionEvent.Caller.HANGUP, cause=EndingCause.CALLER_HANGUP)

    def on_callee_destroyed(self, raw_channel, event):
        print("CALLEE DESTROYED")
        self.machine.final_state = event.get('cause_text')
        if self.machine.channel.redirect_channel:
            cause = EndingCause.CALLEE_ATRANSFERRING_NACCEPTED
        else:
            cause = EndingCause.CALLEE_DESTROYED
        self.cleanup()
        self.machine.change_state(ExtensionEvent.Callee.DESTROYED, cause=cause)

    def on_caller_destroyed(self, raw_channel, event):
        if self.machine.blinded:
            return
        if self.redirected:
            self.redirected = False
            return
        if self.machine.channel.redirect_channel:
            if self.machine.channel.redirect_channel.alive and not self.redirected:
                try:
                    self.events.caller_destroyed.close()
                except Exception as e:
                    logger.error(e)
                self.redirected = True
                self.machine.channel.redirect_channel.raw_channel.unhold()
                self.handlers.bridge.add_channel(channel=self.machine.channel.redirect_channel)
                self.change_caller_channel(channel=self.machine.channel.redirect_channel)
                return

        print("CALLER DESTROYED")
        self.cleanup()
        if self.machine.channel.conferenced_channel is not None:
            self.machine.channel.conferenced_channel.hangup_channel()
        self.machine.next = None
        self.machine.change_state(ExtensionEvent.Caller.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_talking_start(self, raw_channel, event):
        if event['channel']['state'] == SimpleStateType.Channel.UP:
            print(event['channel']['state'])
            print("TALKING STARTED")
            if self.machine.channel.state != SimpleStateType.Channel.UP:
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
        self.machine.final_state = "No Answer"
        if self.machine.extension_webapp.destination_type_no_answer == CallApplicationType.INBOX:
            self.machine.next = (self.machine.extension_webapp.destination_type_no_answer,
                                 self.machine.extension_webapp.extension_number.number)
        else:
            self.machine.next = (self.machine.extension_webapp.destination_type_no_answer,
                                 self.machine.extension_webapp.destination_number_no_answer)

        self.cleanup()
        self.machine.change_state(ExtensionEvent.Callee.NO_ANSWER, cause=EndingCause.CALLEE_NOANSWER)

    def enter(self):
        self.machine.ringing_time = time.time()

        self.events.callee_destroyed = \
            self.machine.callee_channel.raw_channel.on_event(
                SimpleEvent.Channel.DESTROYED,
                self.on_callee_destroyed
            )

        self.events.caller_destroyed = \
            self.machine.channel.raw_channel.on_event(
                SimpleEvent.Channel.DESTROYED,
                self.on_caller_destroyed
            )

        self.events.callee_hangup = \
            self.machine.callee_channel.raw_channel.on_event(
                SimpleEvent.Channel.HANGUP_REQUEST,
                self.on_callee_hungup
            )

        self.events.caller_hangup = self.machine.channel.raw_channel.on_event(
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

    def change_caller_channel(self, channel):
        self.machine.channel = channel
        self.events.caller_destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                     self.on_caller_destroyed)

        self.events.caller_hungup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                  self.on_caller_hungup)
