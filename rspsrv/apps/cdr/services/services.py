import datetime
import json
import logging

import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import status

from rspsrv.apps.call.call_control.channel import ChannelContext
from rspsrv.apps.cdr import models
from rspsrv.apps.cdr.serializers import CDRNSSSerializer
from rspsrv.tools import api_exceptions
from rspsrv.tools.orm import batch as queryset_batch

logger = logging.getLogger("common")


# noinspection PyBroadException
class CDRSendToNSS:
    def __init__(self):
        pass

    @staticmethod
    def send(days):
        date_from = datetime.datetime.now() - datetime.timedelta(days=days)

        queryset = models.CDR.objects.filter(
            Q(call_odate=date_from) &
            Q(direction__in=(ChannelContext.INBOUND, ChannelContext.OUTBOUND))
        )

        url = '{base_url}/{uri}/'.format(base_url=settings.NSS.base_url, uri=settings.NSS.URIs.cdr)

        for result in queryset_batch(queryset, 500):
            serializer = CDRNSSSerializer(result[0], many=True)

            requests.post(
                url,
                data=json.dumps(serializer.data),
            )


class TIO:
    @classmethod
    def get_cdr(cls, params):
        url = '{base_url}/{uri}'.format(base_url=settings.TIO.base_url, uri=settings.TIO.URIs.cdr)

        try:
            page = params.pop("page")
            url += "?page={}".format(page)
            response = requests.get(
                url,
                params=params,
                headers={
                    "Authorization": settings.TIO.AUTH_TOKEN,
                }
            )
        except Exception as e:
            logger.error(e)
            raise api_exceptions.APIException(detail=str(e))

        if not status.is_success(response.status_code):
            raise api_exceptions.raise_exception(
                status_code=response.status_code
            )
        result = response.json() or {}
        return result

    @classmethod
    def get_csv(cls, params):
        url = '{base_url}/{uri}/'.format(base_url=settings.TIO.base_url, uri=settings.TIO.URIs.csv)

        try:
            response = requests.get(
                url,
                params=params,
                headers={
                    "Authorization": settings.TIO.AUTH_TOKEN,
                }
            )
        except Exception as e:
            logger.error(e)
            raise api_exceptions.APIException(detail=str(e))

        if not status.is_success(response.status_code):
            raise api_exceptions.raise_exception(
                status_code=response.status_code
            )
        result = response.json() or {}
        print(result)
        return result
