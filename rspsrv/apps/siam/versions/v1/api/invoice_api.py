from rest_framework import exceptions
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.siam.apps import SiamConfig
from rspsrv.apps.siam.permissions import ApiTokenPermission
from rspsrv.apps.siam.versions.v1.config import SIAMConfigurations
from rspsrv.apps.siam.versions.v1.services.invoice_service import (
    InvoiceService
)
from rspsrv.tools.response import response


class ProductInvoicesAPIView(APIView):
    permission_classes = (ApiTokenPermission,)

    @log_api_request(
        app_name=SiamConfig.name,
        label=SIAMConfigurations.APILabels.GET_INVOICES,
    )
    def get(self, request, number, *args, **kwargs):
        try:
            result = InvoiceService.get_invoices(
                number=number,
                from_datetime=request.GET.get('from_datetime'),
                to_datetime=request.GET.get('to_datetime'),
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(
            request,
            data=(result, None),
        )
