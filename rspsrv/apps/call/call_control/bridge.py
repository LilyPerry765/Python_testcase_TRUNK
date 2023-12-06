import time
import uuid

import requests

from .base import ARIDefaultManager
from .live_recording import LiveRecording


class BridgeType(object):
    MIXING = 'mixing'
    HOLD = 'holding'
    DTMF = 'dtmf_events'
    PROXY = 'proxy_media'


class Bridge(object):
    DefaultHoldingBridge = None

    def __init__(self, bridge, bridge_id, bridge_type):
        self.raw_bridge = bridge
        self.record_handler = None
        self.uid = bridge_id
        self.type = bridge_type
        self.protected = False

    def destroy(self, force=False):
        if self.protected and not force:
            return

        bridge = self.raw_bridge.get()
        for channel_id in bridge.json.get('channels'):
            try:
                self.raw_bridge.removeChannel(channel=channel_id)
            except requests.HTTPError:
                return

        try:
            self.raw_bridge.destroy()
            return True
        except requests.HTTPError as e:
            print("RESP_CODE %s " % e.response.status_code)
            return False

    def close(self, force=False):
        self.destroy(force)

    def remove_channel(self, channels=None, channel=None):
        if channels is not None:
            try:
                iter(channels)
            except TypeError:
                raise TypeError("channels object should be iterable")
            try:
                self.raw_bridge.removeChannel(channel=",".join([channel.uid for channel in channels]))
            except requests.HTTPError as e:
                if e.response.status_code != requests.codes.not_found:
                    raise e
                return False
            except AttributeError:
                raise AttributeError("object's uid attribute not found.")
        if channel is not None:
            try:
                self.raw_bridge.removeChannel(channel=channel.uid)
            except requests.HTTPError as e:
                if e.response.status_code != requests.codes.not_found:
                    raise e
                return False
            except AttributeError:
                raise AttributeError("object's uid attribute not found")

    def add_channel(self, channels=None, channel=None):
        if channels is not None:
            try:
                iter(channels)
            except TypeError:
                raise TypeError("channels object should be iterable.")
            try:
                self.raw_bridge.addChannel(channel=",".join([channel.uid for channel in channels]))
            except requests.HTTPError as e:
                if e.response.status_code != requests.codes.not_found:
                    raise e
                return False
            except AttributeError:
                raise AttributeError("object's uid attribute not found.")

        if channel is not None:
            try:
                self.raw_bridge.addChannel(channel=channel.uid)
            except requests.HTTPError as e:
                if e.response.status_code != requests.codes.not_found:
                    raise e
                return False
            except AttributeError:
                raise AttributeError("object's uid attribute not found.")

        return True

    def start_record(self, path='/~', name=time.time(), max_length=0, max_silence=0,
                     append_on_exist=False, beep=False, reset=False):
        if self.record_handler is not None:
            if reset:
                self.record_handler.stop_and_discard()
            else:
                return self.record_handler

        self.record_handler = LiveRecording.create_record_on_bridge(self, path=path, name=name,
                                                                    max_length=max_length, max_silence=max_silence,
                                                                    append_on_exist=append_on_exist, beep=beep)
        return self.record_handler

    def stop_record(self, save=True):
        if self.record_handler is None:
            return False
        if save:
            self.save_record()
        else:
            self.cancel_record()
        return self.record_handler.path

    def save_record(self):
        if self.record_handler is None:
            return False
        try:
            self.record_handler.stop_and_save()
        except:
            return False
        return self.record_handler.path

    def cancel_record(self):
        if self.record_handler is None:
            return False
        try:
            self.record_handler.stop_and_discard()
        except:
            return False
        return self.record_handler.path

    @staticmethod
    def init_default_holding_bridge():
        if Bridge.DefaultHoldingBridge is None:
            Bridge.DefaultHoldingBridge = HoldingBridge()

    @staticmethod
    def create_bridge(bridge_type, bridge_id=None, name=""):
        """
            :param bridge_type: Bridge type
             :type bridge_type: str
            :param bridge_id: Bridge unique identifier
             :type bridge_id: str
            :param name: Bridge name
             :type name: str
        """
        # bridge_type = [BridgeType.MIXING, BridgeType.DTMF]
        if bridge_id is None:
            bridge_id = uuid.uuid4()
        try:
            bridge = ARIDefaultManager.client.bridges.create(type=bridge_type, name=name, bridgeId=bridge_id)
        except requests.HTTPError:
            return None
        b = Bridge(bridge, bridge_id, bridge_type)
        print("--- BRIDGE CREATED: ", b.uid)
        return b


class HoldingBridge(object):
    def __init__(self, name='', bridge_id=None):
        self.name = name
        self.bridge_id = uuid.uuid4() if bridge_id is None else bridge_id
        self.uid = self.bridge_id
        self.bridge = Bridge.create_bridge(BridgeType.HOLD, bridge_id=self.bridge_id, name=self.name)
        self.raw_bridge = self.bridge.raw_bridge
        self.moh_started = False

    def add_channel(self, channels=None, channel=None):
        self.bridge.add_channel(channels, channel)
        if not self.moh_started:
            try:
                self.bridge.raw_bridge.startMoh()
            except requests.HTTPError:
                pass
            self.moh_started = True

    def remove_channel(self, channels=None, channel=None):
        self.bridge.remove_channel(channels, channel)

