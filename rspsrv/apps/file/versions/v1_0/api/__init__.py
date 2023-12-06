# --------------------------------------------------------------------------
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - api.py
# Created at 2020-4-15,  11:50:2
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import logging

from django.http import HttpResponse
from django.utils.translation import gettext as _
from rest_framework import exceptions
from rest_framework.views import APIView

from rspsrv.apps.file.versions.v1_0.serializers import FileSerializer
from rspsrv.apps.file.versions.v1_0.services import FileService
from rspsrv.tools import response
from rspsrv.tools.permissions import (
    IsSupport,
    IsCustomerAdmin,
    IsCustomerOperator,
    IsFinance,
    IsSales,
    IsSuperUser,
)
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class BaseFileAPIView(APIView):
    permission_classes = [
        IsSupport |
        IsFinance |
        IsSales |
        IsSuperUser |
        IsCustomerAdmin |
        IsCustomerOperator
    ]


class FileAPIView(BaseFileAPIView):
    def get(self, request, file_id):
        try:
            data = FileService.get_file(
                file_id,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        data = FileSerializer(data=data.json()['result'])

        if data.is_valid(raise_exception=True):
            data = data.data

        return response(
            request,
            status=200,
            data=data,
            message=_('Details of file'),
        )


class DownloadFileAPIView(BaseFileAPIView):
    def get(self, request, file_id):
        try:
            data, headers = FileService.download_file(
                file_id,
            )
        except exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        file_response = HttpResponse(
            data,
            content_type=headers['Content-Type'],
        )
        file_response['Content-Disposition'] = headers['Content-Disposition']

        return file_response
