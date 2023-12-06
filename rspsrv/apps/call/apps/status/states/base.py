class ExtensionStatusStateName(object):
    PREAMBLE = 'preamble'
    SET_STATUS = 'set_status'
    ENDING = 'ending'


class ExtensionStatusCommand(object):
    SET_DND = 'dnd'
    SET_AVAILABLE = 'available'
    SET_DISABLE = 'disable'
    SET_FORWARD = 'forward'
    SET_DEFAULT = 'default'
    UNKNOWN = 'unknown'
