import json
import logging
from json import JSONDecodeError

from django.utils.translation import gettext as _
from rest_framework import exceptions, status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.siam.apps import SiamConfig
from rspsrv.apps.siam.permissions import ApiTokenPermission
from rspsrv.apps.siam.versions.v1.config import (
    ResponsesCode,
    SIAMConfigurations,
)
from rspsrv.apps.siam.versions.v1.services.trunk_service import (
    TrunkService
)
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.versions.v1.serializers.subscription import (
    SubscriptionSerializer,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.response import response

logger = logging.getLogger("common")


class BaseSiamAPIView(APIView):
    permission_classes = (ApiTokenPermission,)


class ProductAPIView(BaseSiamAPIView):
    @log_api_request(
        app_name=SiamConfig.name,
        label=SIAMConfigurations.APILabels.GET_PRODUCT,
    )
    def get(self, request, number, *args, **kwargs):
        queryset = Subscription.objects.filter(number=number)

        if not queryset.exists():
            return response(
                request,
                error=_('Subscription <{}> not found!'.format(number)),
                status=status.HTTP_404_NOT_FOUND
            )
        elif queryset.count() > 1:
            return response(
                request,
                error=_('Subscription <{}> not found!'.format(number)),
                status=status.HTTP_404_NOT_FOUND
            )

        serialized_data = SubscriptionSerializer(
            queryset,
            many=True,
        ).data

        return response(request, data=(serialized_data, None))


class ProductSuspendAPIView(BaseSiamAPIView):
    @log_api_request(
        app_name=SiamConfig.name,
        label=SIAMConfigurations.APILabels.SUSPEND_PRODUCT,
    )
    def put(self, request, number, *args, **kwargs):
        try:
            json_params = json.loads(request.body.decode('utf-8'))
        except JSONDecodeError:
            return response(
                request,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=_('Given JSON is not valid!'),
            )

        try:
            result = TrunkService.product_suspend(
                number=number,
                params=json_params,
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code,
                            error=e.detail)

        return response(
            request,
            data=result,
            message=(
                _('siam.msg.success.suspend')
                if result['susp_id'] == 0
                else _('siam.msg.success.release')
            )
        )


class ProductForwardSettingsAPIView(BaseSiamAPIView):
    @log_api_request(
        app_name=SiamConfig.name,
        label=SIAMConfigurations.APILabels.GET_FORWARD_SETTINGS,
    )
    def get(self, request, *args, **kwargs):
        forward_number = request.GET.get('forward_number')
        acceptor_number = request.GET.get('acceptor_number')

        try:
            result = TrunkService.get_forward_settings(
                forwarder=forward_number,
                acceptor=acceptor_number
            )

        except api_exceptions.APIException as e:
            return response(request,
                            status=e.status_code,
                            error=e.detail,
                            hint=e.hint,
                            )

        return response(
            request,
            data=(result, None),
            hint=ResponsesCode.ApplyForwardSettings.SUCCESS_0
        )

    @log_api_request(
        app_name=SiamConfig.name,
        label=SIAMConfigurations.APILabels.UPDATE_FORWARD_SETTINGS,
    )
    def put(self, request, *args, **kwargs):
        json_params = request.data

        try:
            TrunkService.set_forward_settings(
                forwarded_number=json_params['forwarded_number'],
                acceptor_number=json_params['acceptor_number'],
                action=json_params['action'],
                forward_type=json_params['forward_type']
            )
        except api_exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
                hint=e.hint,
            )

        return response(
            request,
            message=_('siam.msg.success.forward'),
            status=status.HTTP_200_OK,
            hint=ResponsesCode.ApplyForwardSettings.SUCCESS_0,
        )
