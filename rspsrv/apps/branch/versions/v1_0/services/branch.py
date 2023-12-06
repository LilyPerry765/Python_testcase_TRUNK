# --------------------------------------------------------------------------
# This service should not be responsible for ACL related tasks
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - branch.py
# Created at 2020-6-15,  13:53:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import logging
from json import JSONDecodeError

from django.utils.translation import gettext as _

from rspsrv.apps.branch.versions.v1_0.config import BranchConfiguration
from rspsrv.apps.cgg.versions.v1_0.services.cgg_service import (
    CggService,
)
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class BranchService:
    @classmethod
    def get_branches(cls, query_params):
        relative_url = BranchConfiguration.URLs.BRANCHES
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
    def add_branch(cls, body):
        relative_url = BranchConfiguration.URLs.BRANCHES
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
    def update_branch(cls, branch, body):
        relative_url = BranchConfiguration.URLs.BRANCH
        relative_url = relative_url.format(
            br=branch,
        )
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
            http_method='patch'
        )

        return response

    @classmethod
    def get_branch(cls, branch):
        relative_url = BranchConfiguration.URLs.BRANCH
        relative_url = relative_url.format(
            br=branch,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            http_method='get'
        )

        return response

    @classmethod
    def delete_branch(cls, branch):
        relative_url = BranchConfiguration.URLs.BRANCH
        relative_url = relative_url.format(
            br=branch,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            http_method='delete'
        )

        return response
