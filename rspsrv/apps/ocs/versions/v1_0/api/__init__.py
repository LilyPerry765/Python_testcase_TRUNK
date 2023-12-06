import json

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.cgg.permissions import APICGRateSInPermission
from rspsrv.apps.ocs.apps import OcsConfig
from rspsrv.apps.ocs.versions.v1_0.config import OcsConfiguration
from rspsrv.apps.ocs.versions.v1_0.services.ocs import (
    OcsService,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.permissions import (
    IsSupport,
    IsFinance,
)
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper


class PeriodicInvoicesAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.PERIODIC_INVOICE,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.periodic_invoices(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Periodic invoices'),
        )


class AutoPayInterimInvoice(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.AUTO_PAY_INTERIM_INVOICE,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.interim_invoice_auto_payed(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Auto pay interim invoice'),
        )


class InterimInvoicesAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.INTERIM_INVOICE,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.interim_invoice(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Interim invoice'),
        )


class PostpaidMaxUsageAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.MAX_USAGE,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.postpaid_max_usage(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Max Usage'),
        )


class OverdueAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.DUE_DATE,
    )
    def post(
            self,
            request,
            warning_type,
            *args,
            **kwargs
    ):
        try:
            OcsService.due_date(
                warning_type,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Due date'),
        )


class DestinationsAPIView(APIView):
    permission_classes = (IsSupport, IsFinance)

    def get(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = OcsService.get_destinations(
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
            status=response_data["status"],
            data=(response_data['data'], None),
            **response_kwargs,
        )


class PrepaidExpiredAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.PREPAID_EXPIRED,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.prepaid_expired(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Prepaid expired'),
        )


class PrepaidRenewedAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.PREPAID_RENEWED,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.prepaid_renewed(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Prepaid renewed'),
        )


class EightyPercentPrepaidAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.EIGHTY_PERCENT_PREPAID,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.prepaid_eighty_percent(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Eighty percent prepaid usage'),
        )


class MaxUsagePrepaidAPIView(APIView):
    permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.MAX_USAGE_PREPAID,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            OcsService.prepaid_max_usage(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Max usage'),
        )


class DeallocationAPIView(APIView):
    #permission_classes = (APICGRateSInPermission,)

    @log_api_request(
        app_name=OcsConfig.name,
        label=OcsConfiguration.APILabels.DEALLOCATION,
    )
    def post(
            self,
            request,
            warning_type,
            *args,
            **kwargs
    ):
        try:
            print('start')
            OcsService.automatic_deallocation(
                warning_type,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
            message=_('Deallocation'),
        )


class RuntimeConfigAPIView(APIView):
    permission_classes = (IsFinance,)

    def get(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = OcsService.get_runtime_configs()
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Runtime configs'),
        )

    def patch(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return response(
                request,
                error=_('JSON is Not Valid'),
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            response_data = OcsService.update_runtime_configs(
                payload,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Set Runtime configs'),
        )
