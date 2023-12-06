from rspsrv.apps.call.apps.base import EndingCause


class ExtensionEvent(object):
    class Callee:
        CREATED = EndingCause.CALLEE_CREATED
        HANGUP = EndingCause.CALLEE_HANGUP
        DESTROYED = EndingCause.CALLEE_DESTROYED
        NO_ANSWER = EndingCause.CALLEE_NOANSWER

        BTRANSFERRED = "callee_redirected"

        ATRANSFERRED = "callee_atransferred"
        ATRANSFERRING = "callee_atransferring"
        ATRANSFERRING_CANCELED = "callee_atransferring_canceled"
        ATRANSFERRING_NACCEPT = "callee_atransferring_naccept"

        CONFERENCED = 'callee_conferenced'

    class Caller:
        DESTROYED = EndingCause.CALLER_DESTROYED
        HANGUP = EndingCause.CALLER_HANGUP

        BTRANSFERRED = "caller_redirected"

        CONFERENCING = "caller_conferencing"
        CONFERENCED = "caller_conferenced"
        CONFERENCING_CANCELED = "caller_conferencing_canceled"

        ATRANSFERRED = "caller_atransferred"
        ATRANSFERRING = "caller_atransferring"
        ATRANSFERRING_CANCELED = "caller_atransferring_canceled"
