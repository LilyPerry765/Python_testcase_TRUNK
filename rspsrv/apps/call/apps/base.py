import threading

import time
import uuid


class CDRAction(object):
    TRANSFERRED = 'transferred'
    CONFERENCED = 'conferenced'


class EndingCause(object):
    CALLER_TRANSFERRED = 'caller_transferred'
    CALLEE_TRANSFERRED = 'callee_transferred'
    CALLEE_CONFERENCED = 'callee_conferenced'
    CALLEE_ATRANSFERRED = 'callee_atransferred'
    CALLEE_ATRANSFERRING_NACCEPTED = 'callee_atransferring_naccepted'
    CALLER_ATRANSFERRED = 'caller_atransferred'
    CALLER_CONFERENCING_CANCELED = 'caller_conferencing_canceled'
    CALLER_ATRANSFERRING_CANCELED = 'caller_atransferring_canceled'
    CALLEE_CREATED = 'callee_created'
    CALLEE_TALKING_START = 'callee_talking'
    CALLER_HANGUP = 'caller_h'
    CALLEE_HANGUP = 'callee_h'
    CALLER_DESTROYED = 'caller_d'
    CALLEE_DESTROYED = 'callee_d'
    CALLEE_NOANSWER = 'callee_noanswer'
    CALLEE_DND = 'callee_dnd'
    CALLEE_DISABLED = 'callee_disabled'
    CALLEE_NAVAILABLE = 'callee_na'
    CALLEE_NEXISTS = 'callee_ne'
    CALLEE_BUSY = 'callee_busy'
    CHANNEL_DESTROYED = 'channel_d'
    CHANNEL_HANGUP = 'channel_h'
    CHANNEL_AUTH_FAILED = 'channel_auth_failed'
    CHANNEL_AUTH_PASSED = 'channel_auth_passed'
    APP_FINISHED = 'app_finish'
    APP_FAILED = 'app_failed'
    APP_TIMEOUT = 'app_timeout'
    APP_OUTOFTIME = 'app_out_of_time'
    APP_CALLER_RESTRICTED = 'app_caller_restricted'
    PLAYBACK_FINISHED = 'playback_finished'
    BILLING_FAILED = 'billing_failed'
    BILLING_ERROR = 'billing_error'
    CALL_RESTRICTED = 'call_restricted'
    MAX_CALL_CONCURRENCY = 'maximum_call_concurrency'
    FAX_RECEIVED_SUCCESS = 'fax_received_success'
    FAX_RECEIVED_FAILED = 'fax_received_failed'
    FAX_SENT_SUCCESS = 'fax_sent_success'
    FAX_SENT_FAILED = 'fax_sent_failed'
    SUBSCRIPTION_DEACTIVATED = 'subscription_deactivated'
    OUTBOUND_DISABLED = 'outbound_disabled'


class AsteriskEndingCause(object):
    NORMAL = 'normal'
    BUSY = 'busy'
    CONGESTION = 'congestion'
    NO_ANSWER = 'no_answer'
    TIMEOUT= 'timeout'
    REJECTED = 'rejected'
    UNALLOCATED = 'unallocated'
    NORMAL_UNSPECIFIED = 'normal_unspecified'
    NUMBER_INCOMPLETE = 'number_incomplete'
    CODEC_MISMATCH = 'codec_mismatch'
    INTERWORKING = 'interworking'
    FAILURE = 'failure'
    ANSWERED_ELSEWHERE = 'answered_elsewhere'


GET_ENDING_CAUSE = {
    'normal': 16,
    'busy': 17,
    'congestion': 34,
    'no_answer': 19,
    'timeout': 18,
    'rejected': 21,
    'unallocated': 1,
    'normal_unspecified': 31,
    'number_incomplete': 28,
    'codec_mismatch': 58,
    'interworking': 127,
    'failure': 38,
    'answered_elsewhere': 26,

    16: 'normal',
    17: 'busy',
    19: 'no_answer',
    20: 'normal',
    31: 'normal_unspecified',
    50: 'unallocated'
}


class CallApplicationType(object):
    end = "end"
    current = "repeat"
    renew = "renew"

    EXTENSION = "extension"
    RING_GROUP = "ringgroup"
    QUEUE = "queue"
    INBOX = "inbox"
    INBOX_PLAY = "inbox_play"
    RECEPTIONIST = "ivr"
    FAX = 'fax'
    EXTERNAL = "out"
    STATUS = "status"
    DATETIME_PLAYBACK = 'datetime_playback'
    DATE_TIME_VR = "date_time_vr"
    EXTENSION_DISPATCHER = "extension_dispatcher"
    CallAgentActivation = "call_queue_agent_activation"
    PLAYBACK = "playback"


class SimpleStateType(object):
    class Channel(object):
        DOWN = "Down"
        RESERVED = "Rsrved"
        OFFHOOK = "OffHook"
        DIALING = "Dialing"
        RING = "Ring"
        RINGING = "Ringing"
        UP = "Up"
        BUSY = "Busy"
        DIALING_OFFHOOK = "Dialing Offhook"
        PRE_RING = "Pre-ring"
        UNKNOWN = "Unknown"


class SimpleEvent(object):
    class Base(object):
        START_MACHINE = "Start"
        TIMEOUT = "Timeout"
        TERMINATE = 'Terminate'
        TIMELY_REJECTION = 'TimelyRejection'
        CALLER_RESTRICTED = 'CallerRestricted'
        CALLEE_BUSY = 'callee_on_another_call'
        SUBSCRIPTION_DEACTIVATED = 'subscription_deactivated'

    class DTMF(object):
        DTMF_1 = "1"
        DTMF_2 = "2"
        DTMF_3 = "3"
        DTMF_4 = "4"
        DTMF_5 = "5"
        DTMF_6 = "6"
        DTMF_7 = "7"
        DTMF_8 = "8"
        DTMF_9 = "9"
        DTMF_0 = "0"
        DTMF_OCTOTHORPE = "#"
        DTMF_STAR = "*"
        DTMF_ANY = "dtmf_any"

    class Channel(object):
        HANGUP_REQUEST = 'ChannelHangupRequest'

        CREATED = 'ChannelCreated'
        DESTROYED = 'ChannelDestroyed'

        DTMF_RECEIVED = 'ChannelDtmfReceived'

        HOLD = 'ChannelHold'
        UNHOLD = 'ChannelUnhold'

        TALKING_FINISHED = 'ChannelTalkingFinished'
        TALKING_STARTED = 'ChannelTalkingStarted'

        RINGING = 'Ringing'
        UP = 'Up'

        STATE_CHANGE = "ChannelStateChange"

        STASIS_START = "StasisStart"

    class Bridge(object):
        ATTENDED_TRANSFER = 'BridgeAttendedTransfer'
        BLIND_TRANSFER = 'BridgeBlindTransfer'
        CREATED = 'BridgeCreated'
        DESTROYED = 'BridgeDestroyed'
        MERGED = 'BridgeMerged'
        VIDEO_SOURCED_CHANGED = 'BridgeVideoSourceChanged'

    class Endpoint(object):
        STATE_CHANGED = 'EndpointStateChange'

    class Playback(object):
        FINISHED = 'PlaybackFinished'
        STARTED = 'PlaybackStarted'
        CHAINED = 'PlaybackChained'

    class Inbox(object):
        MAILBOX_EMPTY = 'empty'

    class Exception(object):
        INBOX_NOT_FOUND = 'inbox_not_found'
        RING_GROUP_NOT_FOUND = 'ring_group_not_found'
        CALL_QUEUE_NOT_FOUND = 'call_queue_not_found'
        AGENT_NOT_FOUND = 'agent_not_found'
        EMPTY_AGENT_QUEUE = 'empty_agent_queue'
        WEB_APP_EXCEPTION = 'web_app_exception'
        ALL_AGENT_ARE_BUSY = 'all_agent_are_busy'

    class Timeout:
        RINGING = 'ringing_timeout'
        GLOBAL = 'global_timeout'

    class Call:
        FINISHED = 'call_finished'
        RESTRICTED = 'call_restricted'
        MAX_CONCURRENCY = 'call_max_concurrency'

    class Application(object):
        # events name shall start with 'App' as a prefix.
        STATE_CHANGED = 'AppStateChanged'
        STARTED = 'AppStarted'
        FINISHED = 'AppFinished'
        TERMINATED = 'AppTerminated'
        ERROR = 'AppError'
        ALL = 'AppEvent'

    class Fax:
        RECEIVE_FAILED = 'fax_received_failed'
        RECEIVE_SUCCESS = 'fax_received_success'
        SEND_FAILED = 'fax_sent_failed'
        SEND_SUCCESS = 'fax_sent_success'


class SimpleTimeout(object):
    def __init__(self, interval, call_back, start=True, *args, **kwargs):
        if not callable(call_back):
            raise TypeError("Call back object is not callable")

        self.__timer = threading.Timer(interval, call_back, *args, **kwargs)
        if start:
            self.start()

    def close(self):
        self.__timer.cancel()

    def start(self):
        self.__timer.start()


class SimpleInterval(object):
    def __init__(self):
        pass


class Dynamics(object):
    class Event(object):
        __slots__ = '__dict__'

        def genocide(self, force=False):
            # for event_name in self.__dict__:
            for event_name in list(self.__dict__):
                if isinstance(event_name, list):
                    for sub_event_name in event_name:
                        try:
                            getattr(self, sub_event_name).close(force)
                        except TypeError:
                            getattr(self, sub_event_name).close()
                        except AttributeError:
                            pass
                else:
                    try:
                        getattr(self, event_name).close(force)
                    except TypeError:
                        getattr(self, event_name).close()
                    except AttributeError:
                        pass

    Handler = Event


class BaseStateMachine(object):
    def __init__(self, **kwargs):
        self.app_name = kwargs.pop('app_name', None)
        self.transitions = {}
        self.current_state = None
        self.history = []
        self.initial_state = None
        self.terminating_state = None
        self.app_states = Dynamics.Handler()

    def add_transition(self, src_state, event, dst_state):
        if src_state.state_name not in self.transitions:
            self.transitions[src_state.state_name] = {}

        self.transitions[src_state.state_name][event] = dst_state

    def machine_change_state(self, event, **kwargs):
        if self.current_state == self.terminating_state:
            return
        self.current_state = self.transitions[self.current_state.state_name].get(event, self.current_state)
        print("Entering %s state" % self.current_state.state_name)
        self.history.append((event, self.current_state))
        self.current_state.enter(**kwargs)

    def machine_start(self, **kwargs):
        if self.initial_state is None or self.terminating_state is None:
            raise Exception("Initial and Terminating states should be declared.")

        self.current_state = self.initial_state
        print("Starting %s state" % self.current_state.state_name)
        self.history.append((SimpleEvent.Base.START_MACHINE, self.initial_state))
        self.current_state.enter(**kwargs)

    def machine_terminate(self, **kwargs):
        print("State machine belongs to %s is going to Terminate" % self.app_name)
        if self.current_state == self.terminating_state:
            return None
        if not self.current_state.unbound:
            self.current_state.cleanup()

        self.current_state = self.terminating_state
        self.history.append((SimpleEvent.Base.TERMINATE, self.current_state))
        self.current_state.enter(**kwargs)

    def get_state_name_on_event(self, event):
        try:
            return self.transitions[self.current_state.state_name][event].state_name
        except (KeyError, AttributeError, ValueError):
            raise ValueError("Current state wont change on given event %s." % event)

    def get_previous(self):
        try:
            return self.history[-2:-1]
        except IndexError:
            pass


class BaseCallApplication(BaseStateMachine):
    class EventHandle(object):
        def __init__(self, app, event_name, name, cb):
            self.event_name = event_name
            self.cb = cb
            self.app = app
            self.name = name

        def close(self):
            try:
                self.app.unsubscribe(self)
            except (ValueError, AttributeError):
                pass

    def __init__(self, channel, target_number=None, **kwargs):
        super(BaseCallApplication, self).__init__(**kwargs)
        self.target_number = target_number

        self.start_time = None
        self.app_states = Dynamics.Handler()
        self.end_time = None

        self.terminated = False

        self.auth_check = kwargs.get('auth_check', False)

        # Tuple of name and exact event name values.
        self.available_events = list(
            filter(lambda k: not k[0].startswith('__'), SimpleEvent.Application.__dict__.items()))

        self.listeners = {str(item[1]): {} for item in self.available_events}

        self.handlers = Dynamics.Handler()
        self.app_states = Dynamics.Handler()

        self.channel = channel

    def __subscribe_is_valid(self, event_name):
        return event_name in self.listeners

    def __execute_assigned_callbacks(self, event_name=None, notify_globals=True, **kwargs):
        listeners = self.listeners if event_name is None else self.listeners.get(event_name, {})

        listeners = listeners.copy()

        for listener_name in listeners:
            if callable(listeners[listener_name]):
                listeners[listener_name](machine_history=self.history, **kwargs)

        if notify_globals:
            listeners = self.listeners.get(SimpleEvent.Application.ALL, {})

            for listener_name in listeners:
                if callable(listeners[listener_name]):
                    listeners[listener_name](machine_history=self.history, **kwargs)

    def on_event(self, event_name, cb):
        if not callable(cb):
            raise TypeError("callback is not callable.")
        if not self.__subscribe_is_valid(event_name):
            raise TypeError("event type %s is not define." % str(event_name))

        name = uuid.uuid4()
        self.listeners[event_name].update({name: cb})
        return self.EventHandle(self, event_name, name, cb)

    def unsubscribe(self, event_handle):
        if event_handle.event_name not in self.listeners:
            raise ValueError
        if self.listeners[event_handle.event_name].pop(event_handle.name, None) is None:
            raise ValueError

    def get_duration(self):
        if self.start_time is None:
            return 0

        if self.end_time is None:
            return time.time() - self.start_time
        else:
            return self.end_time - self.start_time

    def enter(self):
        self.start_time = time.time()

    def end(self, **kwargs):
        force = kwargs.pop('force', False)

        self.end_time = time.time()
        if self.terminated is False:
            self.handlers.genocide(force=force)
            self.__execute_assigned_callbacks(event_name=SimpleEvent.Application.FINISHED, **kwargs)

    def start(self, **kwargs):
        self.machine_start(**kwargs)
        self.__execute_assigned_callbacks(event_name=SimpleEvent.Application.STARTED, **kwargs)

    def change_state(self, event, **kwargs):
        self.machine_change_state(event, **kwargs)
        self.__execute_assigned_callbacks(event_name=SimpleEvent.Application.STATE_CHANGED, **kwargs)

    def terminate(self, **kwargs):
        self.machine_terminate(**kwargs)
        if self.terminated:
            return
        self.terminated = True
        print("TERMINATED")
        self.handlers.genocide()
        self.__execute_assigned_callbacks(event_name=SimpleEvent.Application.TERMINATED, **kwargs)

    def get_name(self):
        raise NotImplementedError

    def get_detail(self):
        raise NotImplementedError

    class WebAppNotExists(Exception):
        pass

    class WebAppRestriction(Exception):
        pass

    class CallAppError(Exception):
        pass


class SimpleState(object):
    state_name = ""

    def __init__(self, **kwargs):
        machine = kwargs.pop("state_machine", kwargs.pop("machine", None))
        if machine is None:
            raise ValueError("State machine arg not found")

        self.events = Dynamics.Event()

        self.unbound = False

        self.machine = machine
        self.handlers = machine.handlers
        self.webapp = kwargs.pop('webapp', None)

    def enter(self, **kwargs):
        raise NotImplementedError

    def cleanup(self, force=False):
        self.events.genocide(force)
        self.unbound = True
