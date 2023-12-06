import logging

from rspsrv.apps.call.apps.base import SimpleState

logger = logging.getLogger("call")


class DeployedReceivingFaxes(object):
    pool = dict()


class ReceivingState(SimpleState):
    state_name = 'receiving'

    def __init__(self, machine, **kwargs):
        super(ReceivingState, self).__init__(machine=machine, **kwargs)

        self.player = None

    def enter(self, **kwargs):
        if kwargs.pop('end', False):
            return

        DeployedReceivingFaxes.pool.update({self.machine.call_id: self})

        self.machine.channel.raw_channel.setChannelVar(variable='CALL_ID', value=self.machine.call_id)
        self.machine.channel.raw_channel.setChannelVar(variable='CALLER_NUMBER',
                                                       value=self.machine.channel.source_number)
        if self.machine.cdr_id:
            self.machine.channel.raw_channel.setChannelVar(variable='CDR_ID', value=self.machine.cdr_id)

        self.machine.channel.raw_channel.continueInDialplan(context='fax-in',
                                                            extension=str(self.machine.target_number))
