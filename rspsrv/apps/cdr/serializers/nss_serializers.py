import re
import socket

from django.conf import settings
from rest_framework import serializers

from rspsrv.apps.call.apps.base import CDRAction
from rspsrv.apps.cdr.models import CDR, CALL_TYPE_CHOICES
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.utils import abnormal_subscription_number
from rspsrv.tools.utility import Operator


class CDRNSSSerializer(serializers.ModelSerializer):
    cdr_id = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    cdr_created_at = serializers.DateTimeField(source='created_at')
    caller = serializers.SerializerMethodField()
    source_ip_port = serializers.SerializerMethodField()
    destination_ip_port = serializers.SerializerMethodField()
    mac_address = serializers.SerializerMethodField()
    in_out_trunk_id = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    call_type = serializers.SerializerMethodField()
    masking_action = serializers.SerializerMethodField()
    masking_value = serializers.SerializerMethodField()
    masked_value = serializers.SerializerMethodField()
    device_serial_number = serializers.SerializerMethodField()
    caller_service_type = serializers.SerializerMethodField()
    caller_location_1 = serializers.SerializerMethodField()
    caller_location_2 = serializers.SerializerMethodField()
    called_service_type = serializers.SerializerMethodField()
    called_location_1 = serializers.SerializerMethodField()
    called_location_2 = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()
    supplementary_service = serializers.SerializerMethodField()
    supplementary_value = serializers.SerializerMethodField()

    class Meta:
        model = CDR
        fields = (
            'cdr_id',
            'domain',
            'cdr_created_at',
            'call_odate',
            'call_otime',
            'caller',
            'called',
            'mask_number',
            'direction',
            'caller_name',
            'called_name',
            'source_ip_port',
            'destination_ip_port',
            'mac_address',
            'in_out_trunk_id',
            'duration',
            'call_type',
            'masking_action',
            'masking_value',
            'masked_value',
            'device_serial_number',
            'caller_service_type',
            'caller_location_1',
            'caller_location_2',
            'called_service_type',
            'called_location_1',
            'called_location_2',
            'action',
            'supplementary_service',
            'supplementary_value',
        )

    class UrlsCache:
        URLS = {

        }

    @staticmethod
    def _get_trunk_id(obj):
        caller = obj.caller or ''
        callee = obj.called or ''

        caller_op = Operator.whois(caller)
        callee_op = Operator.whois(callee)

        if not caller_op or not callee_op:
            return '', ''

        if (
                caller_op['code'] == Operator.Codes.RESPINA and
                callee_op['code'] == Operator.Codes.RESPINA
        ):
            return '', ''

        if caller_op['code'] == Operator.Codes.RESPINA:
            return callee_op['label'], 'callee'

        if callee_op['code'] == Operator.Codes.RESPINA:
            return caller_op['label'], 'caller'

        return '', ''

    @staticmethod
    def _get_location(obj):
        empty = {
            'caller_lat': '',
            'caller_long': '',
            'callee_lat': '',
            'callee_long': '',
        }

        normal_number = None

        if obj.direction == 'outbound':
            normal_number = obj.caller
        elif obj.direction == 'inbound':
            normal_number = obj.called

        if not normal_number:
            return empty

        abnormal_number = abnormal_subscription_number(normal_number)

        if not abnormal_number:
            return empty

        try:
            subscription_obj = Subscription.objects.get(
                number=abnormal_number,
            )
        except Subscription.DoesNotExist:
            return empty

        if obj.direction == 'outbound':
            op = Operator.whois(obj.called)

            return {
                'caller_lat': subscription_obj.latitude,
                'caller_long': subscription_obj.longitude,
                'callee_lat': obj.called if op and op.get('code') in (
                    Operator.Codes.TCT,
                    Operator.Codes.LCT
                ) else '',
                'callee_long': '',
            }

        if obj.direction == 'inbound':
            op = Operator.whois(obj.caller)

            return {
                'caller_lat': obj.caller if op and op.get('code') in (
                    Operator.Codes.TCT,
                    Operator.Codes.LCT
                ) else '',
                'caller_long': '',
                'callee_lat': subscription_obj.latitude,
                'callee_long': subscription_obj.longitude,
            }

        return empty

    @staticmethod
    def _resolve_ip_port(url):
        if url in CDRNSSSerializer.UrlsCache.URLS:
            ip = CDRNSSSerializer.UrlsCache.URLS[url]
        else:
            try:
                ip = socket.gethostbyname(url)
            except socket.gaierror:
                ip = '5.160.247.76'

            CDRNSSSerializer.UrlsCache.URLS[url] = ip

        return ip

    @staticmethod
    def _get_service_type(number):
        op = Operator.whois(number)

        if not op:
            return None

        if op['code'] == Operator.Codes.RESPINA:
            return 3

        if op['code'] in (Operator.Codes.LCT, Operator.Codes.TCT):
            return 0

        if op['code'] in (
                Operator.Codes.Irancell,
                Operator.Codes.MCI,
                Operator.Codes.RighTel
        ):
            return 1

        return None

    @staticmethod
    def get_cdr_id(obj):
        return obj.id

    @staticmethod
    def get_caller(obj):
        if obj.mask_number:
            pattern = r"<sip:([0-9]+)@.+>"
            return re.search(pattern, obj.mask_number).group(1)
        else:
            return obj.caller

    @staticmethod
    def get_source_ip_port(obj):
        if not obj.caller:
            return ''

        if obj.direction == 'outbound':
            return CDRNSSSerializer._resolve_ip_port('{}sbc.nexfon.ir'.format(
                settings.RESPINA_SUB_DOMAIN)
            )
        else:
            return ''

    @staticmethod
    def get_destination_ip_port(obj):
        if not obj.called:
            return ''

        if obj.direction == 'outbound':
            return ''

        if obj.direction == 'inbound':
            trunk = CDRNSSSerializer._get_trunk_id(obj)

            if trunk[1] == '' or trunk[1] == 'caller':
                if len(obj.called) >= 12 and obj.called[:2] == '98':
                    return CDRNSSSerializer._resolve_ip_port(
                        '{}sbc.nexfon.ir'.format(obj.called[2:])
                    )
                else:
                    return CDRNSSSerializer._resolve_ip_port(
                        '{}sbc.nexfon.ir'.format(obj.called)
                    )
            else:
                return ''

    @staticmethod
    def get_mac_address(obj):
        return settings.SBC_MAC

    @staticmethod
    def get_in_out_trunk_id(obj):
        return CDRNSSSerializer._get_trunk_id(obj)[0]

    @staticmethod
    def get_duration(obj):
        return obj.talk_time

    @staticmethod
    def get_call_type(obj):
        """
        According to LI's cdr documentation:
            - Return 1 if cdr is VOIP.
            - Return 5 if cdr is fax.
        :param obj:
        :return:
        """
        if obj.call_type == CALL_TYPE_CHOICES[1][0]:
            # It's Voice Type.
            return 1
        elif obj.call_type == CALL_TYPE_CHOICES[3][0]:
            # It's Fax Type.
            return 5

        return None

    @staticmethod
    def get_masking_action(obj):
        if obj.mask_number:
            return 1

        return 0

    @staticmethod
    def get_masking_value(obj):
        return ''

    @staticmethod
    def get_masked_value(obj):
        return ''

    @staticmethod
    def get_device_serial_number(obj):
        return settings.SBC_MAC.replace(':', '')

    @staticmethod
    def get_caller_service_type(obj):
        return CDRNSSSerializer._get_service_type(obj.caller or '')

    @staticmethod
    def get_caller_location_1(obj):
        return CDRNSSSerializer._get_location(obj)['caller_lat']

    @staticmethod
    def get_caller_location_2(obj):
        return CDRNSSSerializer._get_location(obj)['caller_long']

    @staticmethod
    def get_called_service_type(obj):
        return CDRNSSSerializer._get_service_type(obj.called or '')

    @staticmethod
    def get_called_location_1(obj):
        return CDRNSSSerializer._get_location(obj)['callee_lat']

    @staticmethod
    def get_called_location_2(obj):
        return CDRNSSSerializer._get_location(obj)['callee_long']

    @staticmethod
    def get_action(obj):
        answer = 0
        not_answer = 2
        busy = 3
        unreachable = 4

        if obj.end_cause == 'callee_na':
            return unreachable

        if int(obj.talk_time) > 0:
            return answer

        if int(obj.talk_time) == 0:
            return not_answer

        if obj.end_cause == 'callee_dnd':
            return busy

        return not_answer

    @staticmethod
    def get_supplementary_service(obj):
        if obj.action == CDRAction.TRANSFERRED:
            return '3'
        elif obj.action == CDRAction.CONFERENCED:
            return '4'

        return ''

    @staticmethod
    def get_supplementary_value(obj):
        if obj.action in (CDRAction.TRANSFERRED, CDRAction.CONFERENCED):
            if obj.direction == 'inbound':
                return obj.caller
            elif obj.direction == 'outbound':
                return obj.called

        return ''

    @staticmethod
    def get_domain(obj):
        return settings.RESPINA_SUB_DOMAIN
