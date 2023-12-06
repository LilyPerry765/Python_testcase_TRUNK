from django.conf import settings

from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent
from rspsrv.apps.call.apps.playback.core import Playback


class WaitingState(SimpleState):
    state_name = 'waiting'

    def __init__(self, machine, **kwargs):
        super(WaitingState, self).__init__(machine=machine, **kwargs)

        self.player = None

    def on_player_finished(self, **kwargs):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Playback.FINISHED)

    def on_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST, end=True)

    def on_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED, end=True)

    def enter(self, **kwargs):
        try:
            media = self.machine.inbox_webapp.greeting_file.file.name.split('.')[0]
        except:
            media = settings.DEFAULT_PLAYBACK['BEEP']

        self.events.hangup = self.machine.channel.raw_channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                                       self.on_hangup)

        self.events.destroyed = self.machine.channel.raw_channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                                          self.on_destroyed)
        self.player = Playback(channel=self.machine.channel, target_number=self.machine.target_number,
                               media=media)

        self.handlers.player_finished = self.player.on_event(SimpleEvent.Application.FINISHED, self.on_player_finished)

        self.player.enter()
