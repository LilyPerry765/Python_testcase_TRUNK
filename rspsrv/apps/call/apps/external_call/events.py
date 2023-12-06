from rspsrv.apps.call.apps.base import EndingCause


class ExternalCallEvent(object):
    class Callee:
        CREATED = "Callee_Created"
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

        CONFERENCING = 'caller_conferencing'
        CONFERENCED = 'caller_conferenced'
        CONFERENCING_CANCELED = 'caller_conferencing_canceled'

        ATRANSFERRING = "caller_atransferring"
        ATRANSFERRING_CANCELED = "caller_atransferring_canceled"

    class Transfer:
        CANCELLED = 'Transfer_Cancelled'

    class Conference:
        CANCELLED = 'Conference_Cancelled'
