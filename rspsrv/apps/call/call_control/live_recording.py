import logging
import os
import time

import requests

logger = logging.getLogger("call")


class RecordStat(object):
    RECORDING = 'recording'
    CANCELED = 'canceled'
    SAVED = 'saved'
    PAUSED = 'paused'
    MUTED = 'muted'


class LiveRecordingPool(object):
    recordings = dict()


class LiveRecording(object):
    class IsNotRunning(Exception):
        pass

    class IsRunning(Exception):
        pass

    class IsNotPaused(Exception):
        pass

    class IsPaused(Exception):
        pass

    class IsNotMute(Exception):
        pass

    class IsMute(Exception):
        pass

    def __init__(self, raw_live_recording, observee, name=None, path=None, file_format=None):
        self.raw_live_recording = raw_live_recording
        if name is None:
            name = time.time()
        self.name = name
        self.state = RecordStat.RECORDING
        self.path = path
        self.file_format = file_format
        self.observee = observee
        self.protected = False

        self.on_finished = self.raw_live_recording.on_event("RecordingFinished", self.set_finished)
        self.on_failed = self.raw_live_recording.on_event("RecordingFailed", self.set_failed)

        LiveRecordingPool.recordings.update({self.observee.uid: self})

    def protect(self):
        self.protected = True

    def unprotect(self):
        self.protected = False

    def set_finished(self, raw_recording, event):
        if self.protected:
            return
        self.state = RecordStat.SAVED
        LiveRecordingPool.recordings.pop(self.observee.uid, None)

    def set_failed(self, raw_recording, event):
        self.state = RecordStat.CANCELED
        LiveRecordingPool.recordings.pop(self.observee.uid, None)

    def get_full_name(self):
        # return ".".join((os.path.join(self.path, self.name), self.file_format))
        return ".".join((self.path, self.file_format))

    def stop_and_discard(self):
        if self.state == RecordStat.CANCELED or self.state == RecordStat.SAVED:
            raise LiveRecording.IsNotRunning
        try:
            self.raw_live_recording.cancel()
        except requests.HTTPError as e:
            return False
        except AttributeError:
            raise AttributeError("LiveRecording object is not initialized.")
        LiveRecordingPool.recordings.pop(self.observee.uid, None)
        self.state = RecordStat.CANCELED

    def stop_and_save(self):
        raw_live_recording_should_stop_recording = True

        if self.protected:
            return

        if self.state == RecordStat.CANCELED or self.state == RecordStat.SAVED:
            raise LiveRecording.IsNotRunning

        try:
            self.raw_live_recording.getLive()
        except requests.HTTPError:
            raw_live_recording_should_stop_recording = False

        try:
            if raw_live_recording_should_stop_recording:
                self.raw_live_recording.stop()
                self.state = RecordStat.SAVED
        except requests.HTTPError:
            self.state = RecordStat.CANCELED
            # return
        except AttributeError:
            raise AttributeError("LiveRecording object is not initialized.")
        try:
            LiveRecordingPool.recordings.pop(self.observee.uid)
        except KeyError:
            pass

    def close(self):
        if self.state == RecordStat.SAVED or self.state == RecordStat.CANCELED:
            return
        self.stop_and_save()

    def cancel(self):
        if self.state == RecordStat.SAVED or self.state == RecordStat.CANCELED:
            return
        self.stop_and_discard()

    def pause(self):
        if self.state == RecordStat.PAUSED:
            raise LiveRecording.IsPaused
        try:
            self.raw_live_recording.pause()
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e
            return False
        except AttributeError:
            raise AttributeError("LiveRecording object is not initialized.")
        self.state = RecordStat.PAUSED

    def unpause(self):
        if self.state != RecordStat.PAUSED:
            raise LiveRecording.IsNotPaused
        try:
            self.raw_live_recording.unpause()
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e
            return False
        except AttributeError:
            raise AttributeError("LiveRecording object is not initialized.")
        self.state = RecordStat.RECORDING

    def mute(self):
        if self.state == RecordStat.MUTED:
            raise LiveRecording.IsMute
        try:
            self.raw_live_recording.mute()
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e
            return False
        except AttributeError:
            raise AttributeError("LiveRecording object is not initialized.")
        self.state = RecordStat.MUTED

    def unmute(self):
        if self.state != RecordStat.MUTED:
            raise LiveRecording.IsPaused
        try:
            self.raw_live_recording.unmute()
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e
            return False
        except AttributeError:
            raise AttributeError("LiveRecording object is not initialized.")
        self.state = RecordStat.RECORDING

    @staticmethod
    def create_record_on_bridge(bridge, path='', name=time.time(), file_format='wav', max_length=0, max_silence=0,
                                append_on_exist=False, beep=False):
        if bridge.uid in LiveRecordingPool.recordings:
            return LiveRecordingPool.recordings.get(bridge.uid)

        append_on_exist = "append" if append_on_exist else "overwrite"
        name = str(name)
        full_name = os.path.join(path, name)
        try:
            recording = bridge.raw_bridge.record(name=full_name, format=file_format, maxDurationSeconds=max_length,
                                                 maxSilenceSeconds=max_silence, ifExists=append_on_exist, beep=beep)
        except requests.HTTPError as e:
            if e.response.status_code != requests.codes.not_found:
                raise e
            return False

        return LiveRecording(recording, observee=bridge, name=name, path=full_name, file_format=file_format)

    @staticmethod
    def create_record_on_channel(
            channel,
            path='',
            name=None,
            file_format='wav',
            max_length=0,
            max_silence=0,
            append_on_exist=False,
            beep=False
    ):
        recording = None
        if name is None:
            name = time.time()
        name = str(name)
        full_name = os.path.join(path, name)

        if channel:
            append_on_exist = "append" if append_on_exist else "overwrite"

            if channel.uid in LiveRecordingPool.recordings:
                return LiveRecordingPool.recordings.get(channel.uid)

            try:
                recording = channel.raw_channel.record(
                    name=full_name,
                    format=file_format,
                    maxDurationSeconds=max_length,
                    maxSilenceSeconds=max_silence,
                    ifExists=append_on_exist, beep=beep
                )
            except requests.HTTPError:
                return False

        if recording is None:
            return False

        return LiveRecording(
            recording,
            observee=channel,
            name=name,
            path=full_name,
            file_format=file_format
        )
