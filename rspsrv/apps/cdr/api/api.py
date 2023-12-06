import datetime
import logging
import os
import re

import jdatetime
import jwt
from django.conf import settings
from django.db import connections
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext as _
from rest_framework.views import APIView

from rspsrv.apps.call.call_control.channel import ChannelContext
from rspsrv.apps.cdr.models import CDR, CDRState
from rspsrv.apps.cdr.permissions import CDRPermission
from rspsrv.apps.cdr.serializers import CDRSerializer, CallLogSerializer
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.utils import (
    normalize_outbound_number,
    get_number,
)
from rspsrv.tools.custom_paginator import CustomPaginator
from rspsrv.tools.jalali_date import GregorianConvert
from rspsrv.tools.permissions import (
    IsSupport,
    IsSuperUser,
    IsFinance,
    IsSales,
)
from rspsrv.tools.response import (
    response_ok,
    response500,
    response404,
    response403,
    response400,
)
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class BaseAdminCDRAPIView(APIView):
    permission_classes = [
        IsSuperUser |
        IsSupport |
        IsSales |
        IsFinance
    ]


class ExportCDRToCSVAPIView(BaseAdminCDRAPIView):
    def get(self, request, cdr_id=None):
        lookup_or = {}
        lookup = {'state': 'closed'}
        time_lookup = {}
        if cdr_id:
            lookup.update({'id': cdr_id})

        search_keys = {
            'nf': 'caller',
            'nt': 'called',
            'scf': 'caller_subscription_code',
            'sct': 'callee_subscription_code',
            'ccf': 'caller_customer_id',
            'cct': 'callee_customer_id',
            'lf': 'talk_time__gte',
            'lt': 'talk_time__lte',
            'df': 'call_odate__gte',
            'dt': 'call_odate__lte',
            'cf': 'call_id_prefix',
        }

        for lookup_item in search_keys:
            lookup_value = request.GET.get(lookup_item, None)
            if lookup_value is None:
                continue
            if lookup_item == 'nf':
                if lookup_or:
                    lookup_or = lookup_or & (
                            Q(caller__icontains=lookup_value) | Q(
                        caller_extension__icontains=lookup_value))
                else:
                    lookup_or = Q(caller__icontains=lookup_value) | Q(
                        caller_extension__icontains=lookup_value)

            elif lookup_item == 'nt':
                if lookup_or:
                    lookup_or = lookup_or & (
                            Q(called__icontains=lookup_value) | Q(
                        called_extension__icontains=lookup_value))
                else:
                    lookup_or = Q(called__icontains=lookup_value) | Q(
                        called_extension__icontains=lookup_value)
            else:
                lookup.update({search_keys[lookup_item]: lookup_value})

        time_start_range = datetime.time(int(request.GET.get('hf', 0)) % 24,
                                         int(request.GET.get('mf', 0)) % 60)
        time_end_range = datetime.time(int(request.GET.get('ht', 23)) % 24,
                                       int(request.GET.get('mt', 59)) % 60)
        try:
            queryset = CDR.objects.filter(**lookup)
        except CDR.DoesNotExist:
            return response404(request)
        if lookup_or:
            queryset = queryset.filter(lookup_or)

        if time_start_range > time_end_range:
            time_lookup.update({
                'call_otime__range': sorted(
                    (time_start_range, time_end_range)
                )
            })
            queryset = queryset.exclude(**time_lookup)
        else:
            time_lookup.update(
                {
                    'call_otime__range': (time_start_range, time_end_range)
                }
            )
            queryset = queryset.filter(**time_lookup)
        queryset = Helper.order_by_query(
            CDR,
            queryset,
            request.query_params,
        )
        queryset = queryset.values(
            "id",
            "call_id",
            "call_odate",
            "call_otime",
            "caller",
            "called",
            "duration",
            "talk_time",
            "call_type",
            "call_state",
            "direction",
            "end_cause",
            "state",
            "created_at",
        )
        query, param = queryset.query.sql_with_params()
        final_query = str(query) % tuple(["'{}'".format(s) for s in param])
        data = []
        with connections['cdr_db'].cursor() as cursor:
            cursor.execute(final_query)
            while True:
                row = cursor.fetchone()
                if row is None:
                    break
                row = list(row)
                data.append(
                    [
                        Helper.to_string_for_export(
                            row[0]
                        ),
                        Helper.to_string_for_export(
                            row[1]
                        ),
                        Helper.to_string_for_export(
                            GregorianConvert(
                                date=row[13],
                                timezone='Asia/Tehran',
                            ).jalali_with_time(),
                        ),
                        Helper.to_string_for_export(
                            row[4]
                        ),
                        Helper.to_string_for_export(
                            row[5]
                        ),
                        Helper.to_string_for_export(
                            row[6]
                        ),
                        Helper.to_string_for_export(
                            row[7]
                        ),
                        Helper.to_string_for_export(
                            row[8]
                        ),
                        Helper.to_string_for_export(
                            row[9]
                        ),
                        Helper.to_string_for_export(
                            row[10]
                        ),
                        Helper.to_string_for_export(
                            row[11]
                        ),
                        Helper.to_string_for_export(
                            row[12]
                        ),
                    ]
                )

        header = [
            _("id"),
            _("call id"),
            _("call date"),
            _("caller"),
            _("callee"),
            _("duration"),
            _("talk time"),
            _("call type"),
            _("call state"),
            _("direction"),
            _("end cause"),
            _("state"),
        ]

        return Helper.export_csv(
            request,
            name='cdr',
            data=data,
            header=header,
        )


class CDRAPIView(BaseAdminCDRAPIView):
    def get(self, request, cdr_id=None):
        lookup_or = {}
        lookup = {'state': 'closed'}

        time_lookup = {}

        if cdr_id:
            lookup.update({'id': cdr_id})

        search_keys = {
            'nf': 'caller',
            'nt': 'called',
            'scf': 'caller_subscription_code',
            'sct': 'callee_subscription_code',
            'ccf': 'caller_customer_id',
            'cct': 'callee_customer_id',
            'lf': 'talk_time__gte',
            'lt': 'talk_time__lte',
            'df': 'call_odate__gte',
            'dt': 'call_odate__lte',
            'cf': 'call_id_prefix',
        }

        for lookup_item in search_keys:
            lookup_value = request.GET.get(lookup_item, None)
            if lookup_value is None:
                continue
            if lookup_item == 'nf':
                if lookup_or:
                    lookup_or = lookup_or & (
                            Q(caller__icontains=lookup_value) | Q(
                        caller_extension__icontains=lookup_value))
                else:
                    lookup_or = Q(caller__icontains=lookup_value) | Q(
                        caller_extension__icontains=lookup_value)

            elif lookup_item == 'nt':
                if lookup_or:
                    lookup_or = lookup_or & (
                            Q(called__icontains=lookup_value) | Q(
                        called_extension__icontains=lookup_value))
                else:
                    lookup_or = Q(called__icontains=lookup_value) | Q(
                        called_extension__icontains=lookup_value)
            else:
                lookup.update({search_keys[lookup_item]: lookup_value})

        time_start_range = datetime.time(int(request.GET.get('hf', 0)) % 24,
                                         int(request.GET.get('mf', 0)) % 60)
        time_end_range = datetime.time(int(request.GET.get('ht', 23)) % 24,
                                       int(request.GET.get('mt', 59)) % 60)

        try:
            queryset = CDR.objects.filter(**lookup)
        except CDR.DoesNotExist:
            return response404(request)
        try:
            if lookup_or:
                queryset = queryset.filter(lookup_or)

            if time_start_range > time_end_range:
                time_lookup.update({
                    'call_otime__range': sorted(
                        (time_start_range, time_end_range)
                    )
                })
                queryset = queryset.exclude(**time_lookup)
            else:
                time_lookup.update(
                    {
                        'call_otime__range': (time_start_range, time_end_range)
                    }
                )
                queryset = queryset.filter(**time_lookup)

            queryset = Helper.order_by_query(
                CDR,
                queryset,
                request.query_params,
            )
            queryset, paginator = CustomPaginator().paginate(
                request=request,
                data=queryset,
            )
            serializer = CDRSerializer(
                queryset,
                many=True,
            )
            if cdr_id:
                response_data = serializer.data.pop()
            else:
                response_data = serializer.data, paginator
            return response_ok(request, data=response_data)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class RecordedAudioDownloadAPIView(BaseAdminCDRAPIView):
    def get(self, request, cdr_id, token):
        # Get cdr Payload.
        try:
            payload = Helper.jwt_decode(token=token)
        except jwt.DecodeError as decode_exception:
            return response500(request, error=decode_exception)
        except Exception as any_exception:
            return response500(request, error=any_exception)
        else:
            if 'id' not in payload:
                return response400(request)

            if str(payload['id']) != cdr_id:
                return response403(request)

        # Get The cdr.
        try:
            cdr = CDR.objects.get(id=cdr_id)
        except CDR.DoesNotExist as not_found_exception:
            return response404(request, error=not_found_exception)
        except Exception as any_exception:
            return response500(request, error=any_exception)

        name, extension = os.path.splitext(cdr.recorded_audio.name)

        if extension == '.wav':
            file_name = re.sub(r'\.wav$', '', os.path.basename(
                cdr.recorded_audio.name))

            destination = '{}cdr/{}'.format(
                settings.RECORDED_CALL_LOCATION,
                cdr.call_id,
            )
            if os.path.isfile('{}/{}.mp3'.format(destination, file_name)):
                cdr.recorded_audio = (
                    "cdr/{call_id}/{file_name}".format(
                        call_id=cdr.call_id,
                        file_name='{}.mp3'.format(file_name)
                    )
                )
                cdr.save()

        file = os.path.basename(cdr.recorded_audio.name)

        response = HttpResponse()
        response['X-Accel-Redirect'] = (
            '/storage/cdr/{call_id}/recorded_audio/{file_name}'.format(
                call_id=cdr.call_id,
                file_name=file,
            ))
        response['Content-Disposition'] = (
            'attachment;filename={file_name}'.format(
                file_name=file,
            ))

        return response


class UserCallLogAPIView(BaseAdminCDRAPIView):
    permission_classes = (CDRPermission,)

    def get(self, request):
        extensions = request.user.extension_list.all().values_list(
            'extension_number__number', flat=True)

        queryset = CDR.objects.filter(
            (Q(caller_extension__in=extensions) | Q(
                called_extension__in=extensions) | Q(
                caller__in=extensions) | Q(
                called__in=extensions)),
            state=CDRState.Closed.Value
        ).order_by('-id')[:settings.MAX_CALL_LOG_COUNT]

        queryset, paginator = CustomPaginator().paginate(
            request=request,
            data=queryset,
        )
        serializer = CallLogSerializer(
            queryset,
            many=True,
        )
        response_data = (serializer.data, paginator)

        return response_ok(request, data=response_data)


class GetCallMinutes(BaseAdminCDRAPIView):
    def get(self, request):
        try:
            subscription_obj = Subscription.objects.get(
                number=get_number(request.user.username)
            )
            subscription_number = normalize_outbound_number(
                subscription_obj.number
            )
        except (
                Subscription.DoesNotExist,
                Subscription.MultipleObjectsReturned):
            return response403(request)

        call_minutes = {'incoming': 0, 'outgoing': 0}

        lookup_or = Q(caller=subscription_number) | Q(
            called=subscription_number)

        first_day_of_month = jdatetime.date.today().replace(
            day=1).togregorian()

        cdrs = CDR.objects.filter(lookup_or).filter(
            call_odate__gte=first_day_of_month
        )

        for cdr in cdrs:
            if cdr.talk_time:
                if cdr.direction == ChannelContext.INBOUND:
                    call_minutes['incoming'] += cdr.talk_time
                elif cdr.direction == ChannelContext.OUTBOUND:
                    call_minutes['outgoing'] += cdr.talk_time

        return response_ok(request, data=call_minutes)
