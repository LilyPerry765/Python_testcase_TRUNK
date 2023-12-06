# --------------------------------------------------------------------------
# This service should not be responsible for ACL related tasks
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - cgg_service.py
# Created at 2020-5-29,  11:53:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import logging
from json import JSONDecodeError
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import status

from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class CggService:
    class ResponseType:
        LIST = "list"
        SINGLE = "single"
        EXPORT = "export"

    @classmethod
    def cgg_response(
            cls,
            url,
            body=None,
            http_method='get',
            response_type=ResponseType.SINGLE,
    ):
        if body is None or body == b'':
            body = {}
        if not isinstance(body, dict) and not isinstance(body, list):
            try:
                body = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                raise api_exceptions.ValidationError400(
                    _('JSON is Not Valid')
                )

        headers = {
            'Content-type': 'application/json',
            'Authorization': settings.CGG.AUTH_TOKEN_OUT
        }

        try:
            if http_method in ('patch', 'post'):
                requests_rest_method = getattr(requests, http_method)
                r = requests_rest_method(
                    url=url,
                    json=body,
                    headers=headers,
                    timeout=5.0,
                )
                print(str(r))
            elif http_method == 'delete':
                r = requests.delete(
                    url=url,
                    headers=headers,
                    timeout=5.0,
                )
            else:
                r = requests.get(
                    url=url,
                    json=body,
                    headers=headers,
                    timeout=5.0,
                )
        except requests.exceptions.Timeout:
            raise api_exceptions.RequestTimeout408(
                detail="Timeout on connection to {}".format(url)
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.raise_exception(
                e.status_code,
                e.detail,
            )

        if r.status_code == status.HTTP_204_NO_CONTENT:
            return {
                'status': status.HTTP_204_NO_CONTENT,
                'data': {},
            }
        if response_type == cls.ResponseType.EXPORT:
            if r.status_code == status.HTTP_204_NO_CONTENT or r.status_code \
                    == status.HTTP_200_OK or r.status_code == \
                    status.HTTP_202_ACCEPTED:
                data = {
                    "data": r.content,
                    "status": r.status_code,
                    "content_type": r.headers['Content-Type'],
                    "content_disposition": r.headers['Content-Disposition'],
                }
            else:
                raise api_exceptions.raise_exception(
                    r.status_code,
                    _("No data returned"),
                )
        else:
            try:
                print(str(body))
                data = r.json()
            except JSONDecodeError:
                raise api_exceptions.ValidationError400({
                    'non_fields': _("Received data from CGG in invalid")
                })
        if status.is_success(r.status_code):
            if response_type == cls.ResponseType.LIST:
                response = {
                    'status': data['status'],
                    'data': data['data'],
                    'next': data['next'],
                    'previous': data['previous'],
                    'count': data['count'],
                }
            elif response_type == cls.ResponseType.SINGLE:
                response = {
                    'status': data['status'],
                    'data': data['data'],
                }
            else:
                response = data
            return response
        else:
            raise api_exceptions.raise_exception(
                data['status'],
                data['error'],
            )

    @classmethod
    def cgg_url(
            cls,
            relative_url,
            query_params=None,
    ):
        """
        Return absolute url to CGG Subscription
        :param relative_url: path to API
        :param query_params: Query Dict
        :return:
        """
        if query_params is None:
            query_params = []

        base_url = settings.CGG.API_URL.strip('/')
        relative_url = relative_url.strip('/')

        if query_params:
            query_string = urlencode(query_params)
            return "%s/%s/?%s" % (base_url, relative_url, query_string)

        return "%s/%s/" % (base_url, relative_url)
