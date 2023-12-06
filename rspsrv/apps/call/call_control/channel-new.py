# Deprecated

# from threading import Timer
#
# import requests
# from django.conf import settings
# from switchmanager.local_settings import (
#     SWITCHMANAGER_APP_NAME,
#     CONTROL_TECHNOLOGY, ENDPOINT_CONTEXT,
# )
#
# from rspsrv.apps.call.utils import timer_hangup
# from .base import ARIDefaultManager
# from .iri import IRIManager, ICCManager
# from ..apps.billing.helpers import VoIPBillingSchedule
#
#
# class ChannelFlow(object):
#     INCOMING, OUTGOING, SNOOP, SPY = range(4)
#
#
# class SpyChannelDirection(object):
#     NONE = 'none'
#     BOTH = 'both'
#     OUTGOING = 'out'
#     INCOMING = 'in'
#
#
# SpyAudioDirection = SpyWhisperDirection = SpyChannelDirection
#
#
# class CallManagerChannel(object):
#     def __init__(self, raw_channel, flow, originator=None, billing_cb=None, li_data=None, on_invite=None,
#                  on_hangup=None):
#         """
#
#         :type flow:         ChannelFlow
#         :type originator:   CallManagerChannel
#         :type on_invite:    object
#         :type on_hangup:    object
#         """
#         self.raw_channel = raw_channel
#         self.originator = originator
#         self.terminating = list()
#         self.alive = True
#         self.uid = raw_channel.id
#         self.flow = flow
#         self.bill = False
#         self.billing_callback = billing_cb
#         self.spying = False
#
#         self.iri_controls = list()
#         self.icc_controls = list()
#
#         self.on_hangup = on_hangup
#         self.on_invite = on_invite
#
#         if self.flow == ChannelFlow.INCOMING:
#             self.endpoint_number = self.source_number = raw_channel.json['caller']['number']
#             self.destination_number = self.raw_channel.json['dialplan']['exten']
#             self.caller_id = raw_channel.json['caller']['name']
#         elif self.flow == ChannelFlow.OUTGOING:
#             self.source_number = self.originator.source_number
#             self.caller_id = self.originator.caller_id
#             self.endpoint_number = self.destination_number = self.raw_channel.json['dialplan']['exten']
#
#         if billing_cb:
#             self.billing_control = VoIPBillingSchedule(self.source_number, self.destination_number,
#                                                        self._base_billing_callback)
#             print("Billing started %s" % raw_channel.json['caller']['number'])
#             # self.billing_control.run()
#         else:
#             self.billing_control = None
#
#         if li_data:
#             for li in li_data:
#                 if li.interception_type != 'CC only':
#                     self.iri_controls.append(IRIManager(target_channel=self, li_data=li))
#                 if li.interception_type != 'IRI only':
#                     self.icc_controls.append(ICCManager(target_channel=self, li_data=li))
#
#         if flow == ChannelFlow.INCOMING:
#             self.answer_channel()
#
#     def _base_billing_callback(self, duration):
#         self.billing_callback(self, duration)
#
#     def hangup_channel(self):
#         if self.bill:
#             self.stop_billing()
#         for control in self.iri_controls:
#             control.stop()
#         for control in self.icc_controls:
#             control.stop()
#
#         self.kill_channel()
#
#     def answer_channel(self):
#         self.raw_channel.answer()
#         Timer(
#             settings.MAX_CALL_DURATION_SECONDS,
#             timer_hangup,
#             [self.raw_channel],
#         ).start()
#
#     def kill_channel(self):
#         try:
#             self.raw_channel.hangup()
#         except requests.HTTPError:
#             print("Channel %s Already dropped" % self.uid)
#             return
#         print("Hung up {}".format(self.raw_channel.json.get('name')))
#         self.alive = False
#
#     def start_billing(self):
#         if not self.bill:
#             self.billing_control.run()
#         self.bill = True
#         return True
#
#     def stop_billing(self):
#         if self.bill:
#             self.billing_control.stop()
#         self.bill = False
#         return True
#
#     def get_spy(self, app, spy=SpyAudioDirection.BOTH, whisper=SpyWhisperDirection.NONE, app_args=''):
#         """
#
#             spy: string - Direction of audio to spy on
#                 Default: none
#                 Allowed values: none, both, out, in
#             whisper: string - Direction of audio to whisper into
#                 Default: none
#                 Allowed values: none, both, out, in
#             app: string - (required) Application the snooping channel is placed into
#             appArgs: string - The application arguments to pass to the Stasis application
#             snoopId: string - Unique ID to assign to snooping channel
#
#         :return:
#         """
#         try:
#             snoop_raw_channel = self.raw_channel.snoopChannel(spy=spy, whisper=whisper, app=app, appArgs=app_args)
#         except requests.HTTPError:
#             return None
#         return CallManagerChannel(snoop_raw_channel, ChannelFlow.SNOOP)
#
#     @staticmethod
#     def create_channel(endpoint_number, app_args, endpoint_context=ENDPOINT_CONTEXT, flow=ChannelFlow.OUTGOING,
#                        billing_cb=None, caller_id="respina_sw", li_data=None):
#         """
#             originates a channel and returns CallManagerChannel object
#
#         :param flow:
#         :param li_data:
#         :param endpoint_context:
#         :param caller_id:
#         :param billing_cb:
#         :param endpoint_number: calling number
#         :type endpoint_number: str
#         :param app_args: args
#         :type app_args: str
#         :return: CallManagerChannel
#         """
#         try:
#             if endpoint_number[0] != '/':
#                 endpoint_number = '/' + endpoint_number
#
#             outgoing = ARIDefaultManager.client.channels.originate(
#                 endpoint=CONTROL_TECHNOLOGY + endpoint_number + endpoint_context,
#                 app=SWITCHMANAGER_APP_NAME, callerId=caller_id,
#                 appArgs=app_args)
#             return CallManagerChannel(outgoing, flow, billing_cb=billing_cb, li_data=li_data)
#
#         except requests.HTTPError:
#             return None
#
#     def get_channel_id(self):
#         return self.uid
#
#     def get_endpoint_number(self):
#         if not self.flow == ChannelFlow.SNOOP:
#             return self.endpoint_number
#         return None
#
#
# class IncomingChannel(CallManagerChannel):
#     pass
#
#
# class OutgoingChannel(CallManagerChannel):
#     pass
#
#
# class SnoopChannel(CallManagerChannel):
#     pass
#
#
# class SpyChannel(CallManagerChannel):
#     pass
