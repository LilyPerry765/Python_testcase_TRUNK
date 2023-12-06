# --------------------------------------------------------------------------
# This service should not be responsible for ACL related tasks
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - profit.py
# Created at 2020-6-15,  13:53:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import logging
from json import JSONDecodeError

from django.utils.translation import gettext as _

from rspsrv.apps.cgg.versions.v1_0.services.cgg_service import CggService
from rspsrv.apps.interconnection.versions.v1_0.config import (
    InterconnectionConfiguration,
)
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")

CGG_URLS = InterconnectionConfiguration.URLs


class ProfitService:
    @classmethod
    def add_profit(
            cls,
            body,
    ):
        relative_url = CGG_URLS.PROFITS
        url = CggService.cgg_url(relative_url)
        try:
            body = json.loads(body.decode('utf-8'))
        except JSONDecodeError:
            raise api_exceptions.ValidationError400({
                'non_fields': _('JSON decode error')
            })
        response = CggService.cgg_response(
            url=url,
            body=body,
            http_method='post'
        )

        return response

    @classmethod
    def export_profits(
            cls,
            query_params,
            export_type,
    ):
        relative_url = CGG_URLS.EXPORT_PROFITS
        relative_url = relative_url.format(
            ex_type=export_type,
        )
        url = CggService.cgg_url(
            relative_url,
            query_params,
        )
        response = CggService.cgg_response(
            url=url,
            http_method='get',
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_profits(
            cls,
            query_params,
    ):
        relative_url = CGG_URLS.PROFITS
        url = CggService.cgg_url(
            relative_url,
            query_params,
        )
        response = CggService.cgg_response(
            url=url,
            http_method='get',
            response_type=CggService.ResponseType.SINGLE if
            'bypass_pagination' in query_params else
            CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def get_profit(
            cls,
            profit_id,
    ):
        relative_url = CGG_URLS.PROFIT
        relative_url = relative_url.format(
            pr=profit_id,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            http_method='get'
        )

        return response

    @classmethod
    def update_profit(
            cls,
            profit_id,
            payload,
    ):
        try:
            payload = json.loads(payload.decode('utf-8'))
        except JSONDecodeError:
            raise api_exceptions.ValidationError400({
                'non_fields': _('JSON decode error')
            })
        relative_url = CGG_URLS.PROFIT
        relative_url = relative_url.format(
            pr=profit_id,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            http_method='patch',
            body=payload,
        )

        return response
