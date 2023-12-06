from datetime import datetime

from django.conf import settings
from pyasn1.codec.ber import encoder

from rspsrv.apps.call.apps.base import EndingCause
from rspsrv.apps.subscription.utils import normalize_outbound_number
from .schema import schema


class IRIConstants(object):
    class Version(object):
        V2 = 2
        V3 = 3
        V4 = 4

    class Direction(object):
        NOT_AVAILABLE = 0
        ORIGINATING = 1
        TERMINATING = 2

    class State(object):
        IDLE = 1
        SETUP = 2
        CONNECTED = 3

    class Record(object):
        BEGIN = 'iRI-Begin-record'
        END = 'iRI-End-record'
        CONTINUE = 'iRI-Continue-record'
        REPORT = 'iRI-Report-record'

    class SUPPLEMENTARY_SERVICE(object):
        CFU = 'CFU'  # Call Forward Unconditional
        CW = 'CW'  # Call Waiting
        ECT = 'ECT'  # Explicit Call Transfer
        HOLD = 'Call hold'
        CNF = 'Conference'

    class SERVICE_ACTION(object):
        ACTIVATION = 'NewServiceActivation'
        DEACTIVATION = 'NewServiceDeactivation'
        USING = 'NewServiceUsing'
        TERMINATING = 'NewServiceTerminated'
        ESTABLISHED = 'Established'
        FLOATING = 'Floating'

    class GenericNotifications(object):
        """
        http://alpha.tmit.bme.hu/meresek/ss7p325.htm
        """
        USER_SUSPENDED = 0b0000000
        USER_RESUMED = 0b0000001
        CALL_COMPLETION_DELAY = 0b0000100
        CONFERENCE_ESTABLISHED = 0b1000010
        CONFERENCE_DISCONNECTED = 0b1000011
        OTHER_PARTY_ADDED = 0b1000100
        ISOLATED = 0b1000101
        REATTACHED = 0b1000110
        OTHER_PARTY_ISOLATED = 0b1000111
        OTHER_PARTY_REATTACHED = 0b1001000
        OTHER_PARTY_SPLIT = 0b1001001
        OTHER_PARTY_DISCONNECTED = 0b1001010
        CONFERENCE_FLOATING = 0b1001011
        CALL_IS_A_WAITING_CALL = 0b1100000
        DIVERSION_ACTIVATED = 0b1101000
        CALL_TRANSFER_ALERTING = 0b1101001
        CALL_TRANSFER_ACTIVE = 0b1101010
        REMOTE_HOLD = 0b1111001
        REMOTE_RETRIEVAL = 0b1111010
        CALL_IS_DIVERTING = 0b1111011

    class Nature(object):
        GSM_ISDN = 0
        GSM_SMS = 1
        UUS4 = 2
        TETRA_CALL = 3
        TETRA_DATA = 4
        GPRS_PACKET_DATA = 5

    class PartyQualifier(object):
        ORIGINATING = 0
        TERMINATING = 1
        FORWARDED = 2
        GPRS_TARGET = 3

    # Due to DisconnectReasons from https://en.wikipedia.org/wiki/Q.931
    ReleaseReason = {
        EndingCause.CALLER_TRANSFERRED: 'Normal_call_clearing',
        EndingCause.CALLEE_TRANSFERRED: 'Normal_call_clearing',
        EndingCause.CALLEE_CONFERENCED: 'Normal_call_clearing',
        EndingCause.CALLEE_ATRANSFERRED: 'Normal_call_clearing',
        EndingCause.CALLEE_ATRANSFERRING_NACCEPTED: 'Normal_call_clearing',
        EndingCause.CALLER_ATRANSFERRED: 'Normal_call_clearing',
        EndingCause.CALLER_CONFERENCING_CANCELED: 'Normal_call_clearing',
        EndingCause.CALLER_ATRANSFERRING_CANCELED: 'Normal_call_clearing',
        EndingCause.CALLER_HANGUP: 'Normal_call_clearing',
        EndingCause.CALLEE_HANGUP: 'Normal_call_clearing',
        EndingCause.CALLER_DESTROYED: 'No_user_responding',
        EndingCause.CALLEE_DESTROYED: 'No_user_responding',
        EndingCause.CALLEE_NOANSWER: 'No_answer_from_user',
        EndingCause.CALLEE_DND: 'No_user_responding',
        EndingCause.CALLEE_DISABLED: 'No_user_responding',
        EndingCause.CALLEE_NAVAILABLE: 'No_user_responding',
        EndingCause.CALLEE_NEXISTS: 'No_route_to_destination',
        EndingCause.CALLEE_BUSY: 'User_busy',
        EndingCause.CHANNEL_DESTROYED: 'No_user_responding',
        EndingCause.CHANNEL_HANGUP: 'Normal_call_clearing',
        EndingCause.CHANNEL_AUTH_FAILED: 'Normal_call_clearing',
        EndingCause.CHANNEL_AUTH_PASSED: 'Normal_call_clearing',
        EndingCause.APP_FINISHED: 'Normal_call_clearing',
        EndingCause.APP_FAILED: 'Normal_call_clearing',
        EndingCause.APP_TIMEOUT: 'Normal_call_clearing',
        EndingCause.APP_OUTOFTIME: 'Normal_call_clearing',
        EndingCause.APP_CALLER_RESTRICTED: 'Normal_call_clearing',
        EndingCause.PLAYBACK_FINISHED: 'Normal_call_clearing',
        EndingCause.BILLING_FAILED: 'Normal_call_clearing',
        EndingCause.BILLING_ERROR: 'Normal_call_clearing',
        EndingCause.CALL_RESTRICTED: 'Normal_call_clearing',
        EndingCause.MAX_CALL_CONCURRENCY: 'Normal_call_clearing',
        EndingCause.FAX_RECEIVED_SUCCESS: 'Normal_call_clearing',
        EndingCause.FAX_RECEIVED_FAILED: 'Normal_call_clearing',
        EndingCause.FAX_SENT_SUCCESS: 'Normal_call_clearing',
        EndingCause.FAX_SENT_FAILED: 'Normal_call_clearing',
        EndingCause.SUBSCRIPTION_DEACTIVATED: 'No_route_to_destination'
    }


def ber_encode(wrapper):
    return encoder.encode(wrapper)


def normalize_leg(leg_number):
    return leg_number if leg_number[0:2] == '98' else '98' + leg_number


def e164_format(number):
    # Check Private/UnKnown Number.
    try:
        number = str(int(number))
    except ValueError:
        return 'private_number'

    odd_even = '1' if len(number) % 2 else '0'

    # Set International Bit!
    if number[0:2] == '98':
        first_byte = odd_even + '0000100'
    else:
        first_byte = odd_even + '0000011'

    # According to Customer's Note, "We Don't Parse this Byte" So, It's Not Necessary to Fill it!
    second_byte = '00000000'

    reverse = list()
    i = 0
    while i < len(number):
        two_chars = number[i:i + 2][::-1]
        if len(two_chars) == 1:
            # Zero Is Considered as End of Number.
            two_chars = '0' + two_chars

        reverse.append(two_chars)
        i += 2

    third_byte = ''.join(reverse)

    neid = str(int(first_byte[0:4], 2)) + str(int(first_byte[4:8], 2)) + str(int(second_byte[0:4], 2)) + str(
        int(second_byte[4:8], 2)) + str(int(third_byte))

    return bytes.fromhex(neid)


def generic_notification():
    return 0b00101100


def extension_indicator(leg_index):
    return leg_index


def notification_indicator(supp_type, supp_action):
    result = 0

    if supp_type == IRIConstants.SUPPLEMENTARY_SERVICE.CFU:
        result = IRIConstants.GenericNotifications.CALL_IS_DIVERTING
    elif supp_type == IRIConstants.SUPPLEMENTARY_SERVICE.HOLD:
        result = IRIConstants.GenericNotifications.REMOTE_HOLD
    elif supp_type == IRIConstants.SUPPLEMENTARY_SERVICE.CW:
        result = IRIConstants.GenericNotifications.CALL_IS_A_WAITING_CALL
    elif supp_type == IRIConstants.SUPPLEMENTARY_SERVICE.ECT:
        result = IRIConstants.GenericNotifications.CALL_TRANSFER_ACTIVE
    elif supp_type == IRIConstants.SUPPLEMENTARY_SERVICE.CNF:
        if supp_action == IRIConstants.SERVICE_ACTION.FLOATING:
            result = IRIConstants.GenericNotifications.CONFERENCE_FLOATING
        elif supp_action == IRIConstants.SERVICE_ACTION.ESTABLISHED:
            result = IRIConstants.GenericNotifications.CONFERENCE_ESTABLISHED

    return result + 0b10000000


def dss1_ss_invoke_components(record, supptype):
    """
    ASN Schema 'dSS1-SS-Invoke-components' Tag.
    :return:
    """
    result = None

    if supptype['type'] == IRIConstants.SUPPLEMENTARY_SERVICE.CW:
        if supptype['service_action'] == IRIConstants.SERVICE_ACTION.ACTIVATION:
            result = '810105830102840101'
        elif supptype['service_action'] == IRIConstants.SERVICE_ACTION.DEACTIVATION:
            result = '810105830103840101'

    if supptype['type'] == IRIConstants.SUPPLEMENTARY_SERVICE.CFU:
        if supptype['service_action'] == IRIConstants.SERVICE_ACTION.ACTIVATION:
            result = '810101830102840101'
        elif supptype['service_action'] == IRIConstants.SERVICE_ACTION.DEACTIVATION:
            result = '810101830103840101'

    return result.encode()


def create_packet(record, liid, cin, direction, state, legs, lea_id, duration=None, version=IRIConstants.Version.V4,
                  generalized_time=datetime.now().strftime("%Y%m%d%H%M%S"), target_ip=None,
                  nature=IRIConstants.Nature.GPRS_PACKET_DATA, supps_type=None,
                  end_cause=None, two_legs_only=False, all_legs=False):
    """ Full of nasty hacks...

    :param all_legs:
    :param two_legs_only:
    :param end_cause:
    :param supps_type:
    :param target_ip:
    :param lea_id:
    :param duration:
    :param record:
    :param liid:
    :param cin:
    :param direction:
    :param state:
    :param legs:
    :param version:
    :param generalized_time:
    :param nature:
    :return:
    """
    target_ip = target_ip if target_ip else '0.0.0.0'

    # wrapper initializing
    packet = (schema.IRIsContent())['iRIContent'][record]
    # iri_wrapper['iRIContent'] = None

    # packet = None
    packet['iRIversion'] = version  # default

    packet['lawfulInterceptionIdentifier'] = liid

    packet['communicationIdentifier']['communication-Identity-Number'] = cin

    # Set to 'Respina'.
    packet['communicationIdentifier']['network-Identifier']['operator-Identifier'] = 'Respina'

    # NEID.
    neid_number = ''
    if lea_id == '1':
        neid_number = '307'
    elif lea_id == '2':
        neid_number = '306'
    number = '9156' + neid_number

    packet['communicationIdentifier']['network-Identifier']['network-Element-Identifier']['e164-Format'] = e164_format(
        number
    )

    # packet['timeStamp'] = None
    # packet['timeStamp'][0] = None
    packet['timeStamp']['localTime']['generalizedTime'] = generalized_time  # default

    if direction:
        packet['intercepted-Call-Direct'] = direction

    if state:
        packet['intercepted-Call-State'] = state

    # LineNumber.
    if record == IRIConstants.Record.BEGIN:
        if direction == 1:
            # Caller Is Target.
            packet['locationOfTheTarget']['adslLocation']['lineNumber'] = normalize_leg(legs[0])
        elif direction == 2:
            # Callee Is Target.
            packet['locationOfTheTarget']['adslLocation']['lineNumber'] = normalize_leg(legs[1])

    # IpAddress.
    packet['locationOfTheTarget']['adslLocation']['ipAddress']['iP-type'] = 0
    packet['locationOfTheTarget']['adslLocation']['ipAddress']['iP-value']['iPTextAddress'] = target_ip
    packet['locationOfTheTarget']['adslLocation']['ipAddress']['iP-assignment'] = 1

    # MacAddress.
    if record == IRIConstants.Record.BEGIN:
        packet['locationOfTheTarget']['adslLocation']['macAddress'] = settings.SBC_MAC

    # Movement.
    packet['locationOfTheTarget']['adslLocation']['movement'] = bytes.fromhex('02')

    # packet['partyInformation'] = None

    for index, leg in enumerate(legs):
        party_qualifier = index
        if index == 2 and supps_type and supps_type.get('type', None) == IRIConstants.SUPPLEMENTARY_SERVICE.CNF:
            party_qualifier = index - 1

        if record not in (IRIConstants.Record.CONTINUE, IRIConstants.Record.BEGIN) and index == 2 and not all_legs:
            continue

        if two_legs_only and index >= 2:
            continue

        # Omit '0' at the Start of Leg Number if It's there.
        leg = leg[1:] if leg[0] == '0' else leg

        # Set 'party-Qualifier'.
        packet['partyInformation'][index][0] = party_qualifier

        # Set 'partyIdentity' > 'e164-Format'.
        packet['partyInformation'][index][1][0] = e164_format(normalize_leg(leg))

        # Set 'partyIdentity' > 'sip-uri'.
        if record == IRIConstants.Record.BEGIN:
            packet['partyInformation'][index][1][1] = 'sip:+' + normalize_leg(leg) + "@" + settings.RESPINA_SUB_DOMAIN + \
                                                      '.nexfon.ir'

        # supplementary-services-information
        if supps_type:
            if leg == normalize_outbound_number(supps_type['party_number']):
                # iSUP-SS-parameters
                packet['partyInformation'][index][2][0][0][0] = (
                        hex(generic_notification())[2:] +
                        '0' + hex(extension_indicator(index))[2:] +
                        hex(
                            notification_indicator(
                                supps_type['type'],
                                supps_type['service_action']
                            )
                        )[2:]
                ).encode()

                # dSS1-SS-Invoke-components
                if record == IRIConstants.Record.REPORT:
                    packet['partyInformation'][index][2][0][1] = dss1_ss_invoke_components(record, supps_type)

    packet['nature-Of-The-intercepted-call'] = nature  # default

    if end_cause:
        packet['release-Reason-Of-Intercepted-Call'] = IRIConstants.ReleaseReason.get(end_cause, '')

    if duration:
        duration = int(duration)
        h = int(duration / (60 ** 2))
        m = int((duration % (60 ** 2)) / 60)
        s = duration % 60

        packet['conversationDuration'] = bytes.fromhex("%02d%02d%02d" % (h, m, s))

    # print iri_wrapper.prettyPrint()

    return ber_encode(packet)
