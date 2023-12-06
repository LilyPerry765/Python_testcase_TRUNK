import datetime
import logging
from collections import Counter

import requests
from django.conf import settings

from rspsrv.apps.call.apps.base import SimpleEvent
from rspsrv.apps.call.call_control.base import ARIDefaultManager

logger = logging.getLogger("call")


class EndpointStatus:
    UNKNOWN = 'unknown'
    ONLINE = 'online'
    OFFLINE = 'offline'


class EndpointWatcher(object):
    """There are some effective and non-effective state change call backs which it's necessary to get recognised.
    The previous_state and current_state will handle the effective state-changes and they are useful for
    higher abstractions."""

    def __init__(self, extension_number, technology=settings.CONTROL_TECHNOLOGY, **kwargs):
        self.extension = extension_number
        self.technology = technology
        self.created_at = kwargs.get("timestamp", datetime.datetime.now())

        self.last_update = None
        self.last_status_update = None
        self.last_channels_update = None

        self.associated_channels = []
        self.previous_associated_channels = []
        self.status = EndpointStatus.UNKNOWN
        self.raw_endpoint = None
        self.current_state = None
        self.previous_state = None

        try:
            ARIDefaultManager.client.applications.subscribe(applicationName=settings.SWITCHMANAGER_APP_NAME,
                                                            eventSource="endpoint:%s/%s" %
                                                                        (self.technology, self.extension))
        except requests.HTTPError:
            raise

        self.sync_status()

        if self.status != EndpointStatus.UNKNOWN:
            self.raw_endpoint.on_event(SimpleEvent.Endpoint.STATE_CHANGED, self.on_state_change)

    @staticmethod
    def create_watcher(extension_number, technology=settings.CONTROL_TECHNOLOGY):
        watcher = None
        try:
            watcher = EndpointWatcher(extension_number, technology)
        except requests.HTTPError:
            del watcher
            raise

    def sync_status(self):
        try:
            self.raw_endpoint = ARIDefaultManager.client.endpoints.get(tech=self.technology,
                                                                       resource=self.extension)
        except requests.HTTPError:
            self.status = EndpointStatus.UNKNOWN
            return

        self.status = self.raw_endpoint.json['state']
        self.last_update = datetime.datetime.now()

        channels = self.raw_endpoint.json['channel_ids']

        if Counter(self.associated_channels) != Counter(channels):
            self.previous_associated_channels = self.associated_channels
            self.associated_channels = channels
            self.last_channels_update = self.last_update
        if self.current_state != self.status:
            self.previous_state = self.current_state
            self.current_state = self.status
            self.last_status_update = self.last_update

    def status_changed(self):
        return self.last_update == self.last_status_update

    def channels_changed(self):
        return self.last_update == self.last_channels_update

    def is_online(self, sync=False):
        if sync:
            self.sync_status()
        return self.status == EndpointStatus.ONLINE

    def is_offline(self, sync=False):
        return not self.is_online(sync)

    def on_state_change(self, raw_endpoint, event):
        self.status = raw_endpoint.json['state']
        self.associated_channels = raw_endpoint.json['channel_ids']
        self.last_update = datetime.datetime.now()

        if self.current_state != self.status:
            self.previous_state = self.current_state
            self.current_state = self.status
            self.last_status_update = self.last_update

    def on_event(self, event, callback, **kwargs):
        try:
            return self.raw_endpoint.on_event(event, callback, **kwargs)
        except AttributeError as e:
            logger.error(e)

    def has_channel(self, channel):
        return channel.uid in self.associated_channels

    def __del__(self):
        # noinspection PyBroadException
        try:
            ARIDefaultManager.client.applications.unsubscribe(applicationName=settings.SWITCHMANAGER_APP_NAME,
                                                              eventSource="endpoint:%s/%s" %
                                                                          (self.technology, self.extension))
        except Exception:
            pass
        del self
