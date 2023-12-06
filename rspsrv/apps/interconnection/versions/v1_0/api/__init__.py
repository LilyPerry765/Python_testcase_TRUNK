from datetime import datetime

from django.shortcuts import render
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.interconnection.apps import InterconnectionConfig
from rspsrv.apps.interconnection.versions.v1_0.config import InterconnectionConfiguration
from rspsrv.apps.interconnection.versions.v1_0.services.operator import (
    OperatorService,
)
from rspsrv.apps.interconnection.versions.v1_0.services.profit import (
    ProfitService,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.exporter import Exporter
from rspsrv.tools.permissions import (
    IsSuperUser,
)
from rspsrv.tools.response import response, http_response
from rspsrv.tools.utility import Helper


class OperatorsAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = OperatorService.get_operators(
                request.query_params,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_kwargs = Helper.get_response_kwargs(
            response_data,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(response_data['data'], None),
            **response_kwargs
        )

    @log_api_request(
        app_name=InterconnectionConfig.name,
        label=InterconnectionConfiguration.APILabels.CREATE_OPERATOR
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = OperatorService.add_operator(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Add operators'),
        )


class OperatorAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            operator,
            *args,
            **kwargs
    ):
        try:
            response_data = OperatorService.get_operator(
                operator,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Operator'),
        )

    @log_api_request(
        app_name=InterconnectionConfig.name,
        label=InterconnectionConfiguration.APILabels.UPDATE_OPERATOR
    )
    def patch(
            self,
            request,
            operator,
            *args,
            **kwargs
    ):
        try:
            response_data = OperatorService.update_operator(
                operator,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Update operator'),
        )

    @log_api_request(
        app_name=InterconnectionConfig.name,
        label=InterconnectionConfiguration.APILabels.DELETE_OPERATOR
    )
    def delete(
            self,
            request,
            operator,
            *args,
            **kwargs
    ):
        try:
            response_data = OperatorService.delete_operator(
                operator,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data['status'],
            data=response_data['data'],
            message=_('Remove operator'),
        )


class ExportProfitsAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            export_type,
            *args,
            **kwargs
    ):
        try:
            data = ProfitService.export_profits(
                request.query_params,
                export_type,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return http_response(data)


class ProfitsAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = ProfitService.get_profits(
                request.query_params,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        response_kwargs = Helper.get_response_kwargs(
            response_data,
            self.request.get_host(),
            self.request.path_info,
        )
        return response(
            request,
            data=(response_data['data'], None),
            **response_kwargs,
        )

    @log_api_request(
        app_name=InterconnectionConfig.name,
        label=InterconnectionConfiguration.APILabels.CREATE_PROFIT
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = ProfitService.add_profit(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Add profit'),
        )


class DownloadProfitAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            profit,
            *args,
            **kwargs
    ):
        try:
            data = ProfitService.get_profit(
                profit,
            )["data"]
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        data['inbound_usage'] = Helper.convert_nano_seconds_to_minutes(
            data['inbound_usage'],
        )
        data['outbound_usage'] = Helper.convert_nano_seconds_to_minutes(
            data['outbound_usage'],
        )

        if request.GET.get('html'):
            return render(request, 'profit.html', {
                'profit': data,
            })

        try:
            return Exporter(request).export(
                filename="profit - {}".format(
                    str(datetime.now().timestamp())
                ),
                template='profit.html',
                data={
                    'profit': data,
                },
            )
        except Exception as e:
            return response(
                request,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=e,
            )


class ProfitAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            profit,
            *args,
            **kwargs
    ):
        try:
            response_data = ProfitService.get_profit(
                profit,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Profit'),
        )

    @log_api_request(
        app_name=InterconnectionConfig.name,
        label=InterconnectionConfiguration.APILabels.UPDATE_PROFIT
    )
    def patch(
            self,
            request,
            profit,
            *args,
            **kwargs
    ):

        try:
            response_data = ProfitService.update_profit(
                profit,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Update profit'),
        )
