import uuid

from rspsrv.apps.call.call_control.types import CallType
from rspsrv.apps.cdr.models import CDR, GET_CALL_TYPE_INT

call_pool = list()


class CallManagerPool(object):
    total_calls = 0
    active_calls = 0
    total_spied_calls = 1

    def __init__(self, name=None):
        try:
            last_cdr = CDR.objects.filter(call_type=GET_CALL_TYPE_INT[CallType.VOICE]).latest('call_id')
            self.current_call_id = last_cdr.call_id
        except CDR.DoesNotExist:
            self.current_call_id = 1

        if name is None:
            self.name = uuid.uuid4()
        else:
            self.name = name

    def inc(self):
        self.current_call_id += 1

        return self.current_call_id

    def issue_call_id(self, channel):
        if channel is not None:
            return channel.call_id or str(self.inc())
        return str(self.inc())


DefaultCallManagerPool = CallManagerPool()
