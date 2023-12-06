from rspsrv.apps.call.apps.base import SimpleEvent
from rspsrv.apps.call.call_control.endpoint import EndpointWatcher, EndpointStatus
from rest_framework import exceptions


class EndpointStateManagerPool(object):
    """Provides a high level abstraction layer which maps the assumed channels
       to desired endpoints."""

    def __init__(self, extension_numbers, on_endpoint_down=None, on_endpoint_up=None,
                 on_channel_acquisition=None, on_channel_release=None):
        """
        :param extension_numbers: list of integers representing existing Extensions
        :type  extension_numbers: list
        :param on_endpoint_down: a call-back which it will be called on endpoint down
        :type  on_endpoint_down: function
        :param on_endpoint_up: a call-back which it will be called on endpoint up
        :type  on_endpoint_up: function
        :param on_channel_acquisition: a call-back which it will be called on channel assignments to the endpoint.
        :type  on_channel_acquisition: function
        :param on_channel_release: a call-back which it will be called on channel releasing of an endpoint.
        :type  on_channel_release: function
        """

        if not isinstance(extension_numbers, (list, tuple)):
            raise TypeError('extension_numbers should be a list or set of extensions, %s is given.'
                            % type(extension_numbers))

        self.extensions = extension_numbers

        if on_channel_release and not callable(on_channel_release):
            raise TypeError('on_channel_release should be callable, %s is given' % type(on_channel_release))
        if on_channel_acquisition and not callable(on_channel_acquisition):
            raise TypeError('on_channel_acquisition should be callable, %s is given' % type(on_channel_acquisition))
        if on_endpoint_down and not callable(on_endpoint_down):
            raise TypeError('on_endpoint_down should be callable, %s is given' % type(on_endpoint_down))
        if on_endpoint_up and not callable(on_endpoint_up):
            raise TypeError('on_endpoint_up should be callable, %s is given' % type(on_endpoint_up))

        self.on_endpoint_down_cb = on_endpoint_down
        self.on_endpoint_up_cb = on_endpoint_up
        self.on_channel_acquisition = on_channel_acquisition
        self.on_channel_release = on_channel_release

        self.watchers = []
        for extension in self.extensions:
            # noinspection PyBroadException
            try:
                self.watchers.append(EndpointWatcher(extension))
            except Exception:
                pass
        for watcher in self.watchers:
            watcher.on_event(SimpleEvent.Endpoint.STATE_CHANGED, self.__on_endpoint_state_change, watcher=watcher)

    def __on_endpoint_state_change(self, raw_endpoint, event, watcher):
        if watcher.status_changed():
            if watcher.current_state == EndpointStatus.ONLINE:
                self.__on_endpoint_up_base_callback(watcher)
            elif watcher.current_state == EndpointStatus.OFFLINE:
                self.__on_endpoint_down_base_callback(watcher)

        if watcher.channels_changed():
            acquisitions = list(set(watcher.associated_channels) - set(watcher.previous_associated_channels))
            releases = list(set(watcher.previous_associated_channels) - set(watcher.associated_channels))

            for ac in acquisitions:
                self.__on_channel_acquisition_base_callback(ac, watcher)
            for re in releases:
                self.__on_channel_release_base_callback(re, watcher)

    def __on_endpoint_down_base_callback(self, watcher):
        if self.on_endpoint_down_cb is not None:
            self.on_endpoint_down_cb(watcher)

    def __on_endpoint_up_base_callback(self, watcher):
        if self.on_endpoint_up_cb is not None:
            self.on_endpoint_up_cb(watcher)

    def __on_channel_acquisition_base_callback(self, channel_id, watcher):
        if self.on_channel_acquisition is not None:
            self.on_channel_acquisition(channel_id, watcher)

    def __on_channel_release_base_callback(self, channel_id, watcher):
        if self.on_channel_release is not None:
            self.on_channel_release(channel_id, watcher)

    def get_endpoint_status(self, extension_number):
        for watcher in self.watchers:
            if watcher.extension == extension_number:
                return watcher.status
        return None

    def is_endpoint_online(self, extension_number):
        for watcher in self.watchers:
            if watcher.extension == extension_number:
                return watcher.is_online(sync=True)
        raise exceptions.NotFound

    def is_endpoint_offline(self, extension_number):
        for watcher in self.watchers:
            if watcher.extension == extension_number:
                return watcher.is_offline(sync=True)
        raise exceptions.NotFound

    def set_on_endpoint_up(self, on_endpoint_up):
        if on_endpoint_up and not callable(on_endpoint_up):
            raise TypeError('on_endpoint_up should be callable, %s is given' % type(on_endpoint_up))

        self.on_endpoint_up_cb = on_endpoint_up

    def set_on_endpoint_down(self, on_endpoint_down):
        if on_endpoint_down and not callable(on_endpoint_down):
            raise TypeError('on_endpoint_up should be callable, %s is given' % type(on_endpoint_down))

        self.on_endpoint_down_cb = on_endpoint_down

    def unsubscribe_callbacks(self):
        self.on_endpoint_down_cb = None
        self.on_endpoint_up_cb = None


EndpointPool = EndpointStateManagerPool
