class CallState(object):
    SETUP = 'setup'
    RINGING = 'ringing'
    CONNECTED = 'connected'
    TRANSFERRED = 'transferred'
    TERMINATED = 'terminated'
    DONE = 'done'


class CallType(object):
    SMS = 'SMS'
    VOICE = 'Voice'
    VIDEO = 'Video'
    CHAT = 'Chat'
    FAX = 'Fax'

