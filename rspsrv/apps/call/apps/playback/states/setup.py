import requests

from rspsrv.apps.call.apps.base import SimpleState, SimpleEvent
from rspsrv.apps.call.apps.playback.states.base import PlaybackLogic
from rspsrv.apps.call.apps.playback.states.base import PlaybackStateName


class SetupState(SimpleState):
    state_name = PlaybackStateName.SETUP

    def __init__(self, machine, **kwargs):
        super(SetupState, self).__init__(state_machine=machine, **kwargs)

    def on_playback_started(self, raw_playback, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Playback.STARTED)

    def on_channel_hangup(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.HANGUP_REQUEST)

    def on_channel_destroyed(self, raw_channel, event):
        self.cleanup()
        self.machine.change_state(SimpleEvent.Channel.DESTROYED)

    def enter(self, **kwargs):

        if self.machine.logic != PlaybackLogic.TIME:
            preface = "%s:" % self.machine.logic
            try:
                self.machine.player = self.machine.channel.raw_channel.playWithId(playbackId=self.machine.playback_id,
                                                                                  media=preface + str(self.machine.playback))
            except requests.exceptions.HTTPError:
                pass
        else:
            preface = "%s:" % PlaybackLogic.MEDIA
            try:
                self.machine.player = self.machine.channel.raw_channel.playWithId(playbackId=self.machine.playback_id,
                                                                                  media=preface + self.machine.playback)
            except requests.exceptions.HTTPError:
                pass

        if self.machine.player:
            self.events.playback_started = self.machine.player.on_event(SimpleEvent.Playback.STARTED,
                                                                        self.on_playback_started)

        self.events.hangup = self.machine.channel.on_event(SimpleEvent.Channel.HANGUP_REQUEST,
                                                           self.on_channel_hangup)
        self.events.destroyed = self.machine.channel.on_event(SimpleEvent.Channel.DESTROYED,
                                                              self.on_channel_destroyed)
