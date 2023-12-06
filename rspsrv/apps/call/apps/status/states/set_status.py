from django.conf import settings

from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent, EndingCause, SimpleTimeout
from rspsrv.apps.call.apps.playback.core import Playback
from rspsrv.apps.call.apps.status.states.base import ExtensionStatusStateName, ExtensionStatusCommand


class SetStatusState(SimpleState):
    state_name = ExtensionStatusStateName.SET_STATUS

    def __init__(self, machine, **kwargs):
        super(SetStatusState, self).__init__(machine=machine, **kwargs)
        self.forward_number = ""
        self.command = None

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, cause=EndingCause.CALLER_DESTROYED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, cause=EndingCause.CALLER_HANGUP)

    def on_timeout(self, **kwargs):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Timeout.GLOBAL, cause=EndingCause.APP_TIMEOUT)

    def on_bad_command(self, **kwargs):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Base.TERMINATE, cause=EndingCause.APP_FINISHED)

    def on_saving(self, **kwargs):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Base.TERMINATE, cause=EndingCause.APP_FINISHED)

    def on_dtmf_received(self, raw_channel, event):
        digit = event.get('digit')
        if digit.isdigit():
            self.forward_number += digit
        elif digit == SimpleEvent.DTMF.DTMF_STAR:
            self.events.saving_playback = Playback(channel=self.machine.channel,
                                                   media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                   ['STATUS_SAVE'])
            self.events.not_saving_playback = Playback(channel=self.machine.channel,
                                                       media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                       ['STATUS_NOT_SAVE'])

            if self.command == ExtensionStatusCommand.SET_FORWARD:
                if self.forward_number.isdigit():
                    self.machine.extension_webapp.forward_to = self.forward_number
                    self.machine.extension_webapp.status = self.command
                    self.machine.extension_webapp.save()

                    self.events.saving_playback.on_event(SimpleEvent.Application.FINISHED, self.on_saving)
                    self.events.saving_playback.enter()
                else:
                    self.events.not_saving_playback.on_event(SimpleEvent.Application.FINISHED, self.on_timeout)
                    self.events.not_saving_playback.enter()
            else:
                self.events.saving_playback.on_event(SimpleEvent.Application.FINISHED, self.on_saving)
                self.events.saving_playback.enter()
                self.machine.extension_webapp.forward_to = None
                self.machine.extension_webapp.status = self.command \
                    if self.command != ExtensionStatusCommand.SET_DEFAULT else ExtensionStatusCommand.SET_AVAILABLE
                self.machine.extension_webapp.save()

    def enter(self, **kwargs):
        self.command = kwargs.pop('command', None)
        print('command is: ', self.command)
        if self.command is None or self.command == ExtensionStatusCommand.UNKNOWN:
            self.events.bad_command_playback = Playback(channel=self.machine.channel,
                                                        media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                        ['BAD_COMMAND'])
            self.events.bad_command_playback.on_event(SimpleEvent.Application.FINISHED, self.on_bad_command)
            self.events.bad_command_playback.enter()
            return

        self.events.timeout = SimpleTimeout(60, self.on_timeout)
        self.events.on_dtmf = self.machine.channel.on_event(SimpleEvent.Channel.DTMF_RECEIVED, self.on_dtmf_received)

        self.events.ask_to_save_playback = Playback(channel=self.machine.channel,
                                                    media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                    ['ASK_TO_SAVE'])

        if self.command == ExtensionStatusCommand.SET_DEFAULT or self.command == ExtensionStatusCommand.SET_AVAILABLE:
            self.events.status_playback = Playback(channel=self.machine.channel,
                                                   media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                   ['AVAILABLE'])

        elif self.command == ExtensionStatusCommand.SET_DND:
            self.events.status_playback = Playback(channel=self.machine.channel,
                                                   media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                   ['DND'])

        elif self.command == ExtensionStatusCommand.SET_FORWARD:
            self.events.status_playback = Playback(channel=self.machine.channel,
                                                   media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                   ['FORWARD'])

            self.events.ask_to_save_playback = Playback(channel=self.machine.channel,
                                                        media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                        ['ASK_TO_SAVE_FORWARD'])

        self.events.change_status_to_playback = Playback(channel=self.machine.channel,
                                                         media=settings.DEFAULT_PLAYBACK['EXTENSION_STATUS']
                                                         ['CHANGE_STATUS_TO'])

        self.events.change_status_to_playback.enter()
        self.events.change_status_to_playback.on_event(SimpleEvent.Application.FINISHED,
                                                       self.events.status_playback.enter)
        self.events.status_playback.on_event(SimpleEvent.Application.FINISHED,
                                             self.events.ask_to_save_playback.enter)

        return
