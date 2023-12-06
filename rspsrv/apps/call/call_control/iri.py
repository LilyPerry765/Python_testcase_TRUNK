import binascii
import json
import logging
import time
import uuid
from datetime import datetime
from threading import Timer, Thread

import requests
from django.conf import settings

from rspsrv.apps.call.call_control.channel import ChannelContext
from rspsrv.apps.subscription.utils import normalize_outbound_number
from rspsrv.tools.sbc import SBC
from .call_pool import LI
from ..asn.asn_mod import IRIConstants, create_packet

logger = logging.getLogger("call")


# from ..local_settings import HI2_INTERVAL,HI2_SEND_TIMEOUT, SWITCHMANAGER_APP_NAME, OPERATOR_IDENTIFIER, SBC_PUBLIC_IP
# from ..local_settings import LIGate


class IRIManager(object):
    def __init__(self, target_channel, li_data, active=True, **kwargs):
        """
        :type target_channel: CallManagerChannel
        """

        self.uid = uuid.uuid4()
        self.target_channel = target_channel
        self.affected_channel = None
        self.affected_number = kwargs.pop('affected_number', None)

        # Determine Target IP.
        self.subscription_number = kwargs.pop('subscription_number', None)
        self.target_ip = SBC.get_user_ip(self.subscription_number)

        self.ftp_address = li_data.ftp_address
        self.ftp_port = li_data.ftp_port
        self.ftp_type = li_data.ftp_type
        self.ftp_username = li_data.ftp_username
        self.ftp_password = li_data.ftp_password
        self.lea_id = li_data.lea_id

        self.liid = li_data.liid

        self._direction = {
            ChannelContext.INBOUND: 2,
            ChannelContext.OUTBOUND: 1
        }.get(target_channel.context, 0)

        self.subscription = kwargs.pop('subscription', None)

        self._cin = LI.get_cin()

        print("DESTINATION NUMBER", target_channel.destination_number)
        print("SOURCE NUMBER", target_channel.source_number)
        if target_channel.context == ChannelContext.INBOUND:
            if target_channel.mask_number:
                originating_party = normalize_outbound_number(target_channel.mask_number)
            else:
                originating_party = normalize_outbound_number(target_channel.source_number)
            self._legs = [originating_party,
                          normalize_outbound_number(target_channel.destination_number)]
        else:
            self._legs = [
                normalize_outbound_number(self.subscription.number),
                normalize_outbound_number(
                    target_channel.destination_number,
                )
            ]

        self._time = datetime.now().strftime("%Y%m%d%H%M%S")

        self._start_time = time.time()

        self._record = IRIConstants.Record.BEGIN

        self.state = IRIConstants.State.SETUP

        self.index = 1

        self.is_running = True

        # internal objects:
        self._timer = None
        self.sched_set = False
        self._interval = settings.HI2_INTERVAL
        self._total_packets = 0

        if active:
            report = self._make_report()
            self._send_report(report)

    def _sched_restart(self):
        if self.sched_set:
            self._sched_stop()
            self._sched()

    def _sched(self):
        if not self.sched_set:
            print('_sched', self._interval)
            self._timer = Timer(self._interval, self._run)
            self._timer.start()
            self.sched_set = True

        self.is_running = True

    def _sched_stop(self):
        if self._timer:
            self._timer.cancel()
        self.is_running = False

    def _run(self, supps_type=None):
        if not supps_type:
            if self._record != IRIConstants.Record.BEGIN:
                self.sched_set = False
                self._sched_stop()
                self._sched()
            print('_run')
        report = self._make_report(supps_type=supps_type)
        self._send_report(report)

    def _make_report(self, supps_type=None, end_cause=None, two_legs_only=False,
                     all_legs=False):
        if self._record == IRIConstants.Record.END:
            du = time.time() - self._start_time
        else:
            du = None

        ber_report = create_packet(
            record=self._record,
            liid=self.liid,
            cin=self._cin,
            direction=self._direction,
            state=self.state,
            legs=self._legs,
            duration=du,
            generalized_time=self._time,
            lea_id=self.lea_id,
            target_ip=self.target_ip,
            supps_type=supps_type,
            end_cause=end_cause,
            two_legs_only=two_legs_only,
            all_legs=all_legs
        )

        return {"url": self.ftp_address, "port": self.ftp_port, "username": self.ftp_username,
                "password": self.ftp_password, "type": self.ftp_type, "index": self.index, "liid": self.liid,
                "cin": self._cin, "data": str(binascii.hexlify(ber_report))}

    def _send_worker(self, report):
        while True:
            try:
                requests.post(settings.LI_GATE.HOST + settings.LI_GATE.Requests.ftp_mediator, data=json.dumps(report),
                              timeout=settings.HI2_SEND_TIMEOUT)
            except requests.RequestException as e:
                continue

            return True

    def _send_report(self, report):
        self.index += 1
        t = Thread(target=self._send_worker, args=(report,))
        t.daemon = True
        t.start()

    def set_record_begin(self, supps_type=None):
        self.set_state_setup()
        self._record = IRIConstants.Record.BEGIN
        self._run(supps_type=supps_type)
        return True

    def set_record_continue(self, supps_type=None):
        self.set_state_connected()
        self._record = IRIConstants.Record.CONTINUE
        self._run(supps_type=supps_type)
        return True

    def set_record_report(self):
        self._record = IRIConstants.Record.REPORT
        self._run()
        return True

    def set_supps_act_record_report(self, supps_type):
        self._record = IRIConstants.Record.REPORT
        self._run(supps_type=supps_type)
        return

    def set_supps_deact_record_report(self, supps_type):
        self._record = IRIConstants.Record.REPORT
        self._run(supps_type=supps_type)
        return

    def set_record_end(self, end_cause=None, two_legs_only=False, all_legs=False):
        if not self.is_running:
            return

        self._sched_stop()
        self._record = IRIConstants.Record.END
        self.set_state_idle()
        report = self._make_report(end_cause=end_cause, two_legs_only=two_legs_only,
                                   all_legs=all_legs)
        self._send_report(report)

    def set_state_setup(self):
        self.state = IRIConstants.State.SETUP

    def set_state_connected(self):
        self.state = IRIConstants.State.CONNECTED

    def set_state_idle(self):
        self.state = IRIConstants.State.IDLE

    def set_forwarded_to_party(self, forwarded_party_number):
        self._legs.append(
            normalize_outbound_number(forwarded_party_number)
        )

    def set_conferenced_to_party(self, conferenced_party_number):
        self._legs.append(
            normalize_outbound_number(conferenced_party_number)
        )
        self._issue_cin()
        self.is_running = True

    def run(self):
        self._run()

    def stop(self):
        pass

    def change_target_channel(self, channel):
        self.target_channel = channel

    def get_cin(self):
        return self._cin

    def _issue_cin(self):
        self._cin = LI.issue_cin()

    def re_active(self):
        self.is_running = True


class SupplementaryIRIReport(object):
    def __init__(self, target_number, li_data, supps_type):
        self.target_number = target_number
        self.supps_type = supps_type

        self._time = datetime.now().strftime("%Y%m%d%H%M%S")

        self.index = 1

        self.ftp_address = li_data.ftp_address
        self.ftp_port = li_data.ftp_port
        self.ftp_type = li_data.ftp_type
        self.ftp_username = li_data.ftp_username
        self.ftp_password = li_data.ftp_password
        self.lea_id = li_data.lea_id

        self.liid = li_data.liid

        self._cin = LI.get_cin()

        self._legs = [normalize_outbound_number(target_number)]

    def make_report(self):
        ber_report = create_packet(
            record=IRIConstants.Record.REPORT,
            liid=self.liid,
            cin=self._cin,
            direction=None,
            state=None,
            legs=self._legs,
            generalized_time=self._time,
            lea_id=self.lea_id,
            target_ip=None,
            supps_type=self.supps_type,
        )

        return {"url": self.ftp_address, "port": self.ftp_port, "username": self.ftp_username,
                "password": self.ftp_password, "type": self.ftp_type, "index": self.index, "liid": self.liid,
                "cin": self._cin, "data": str(binascii.hexlify(ber_report))}

    def send_report(self):
        report = self.make_report()

        while True:
            try:
                requests.post(settings.LI_GATE.HOST + settings.LI_GATE.Requests.ftp_mediator, data=json.dumps(report),
                              timeout=settings.HI2_SEND_TIMEOUT)
            except requests.RequestException as e:
                continue

            return True
