from django.utils.translation import gettext as _
from rest_framework import exceptions, status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.crm.apps import CrmConfig
from rspsrv.apps.crm.configs import CrmConfigurations
from rspsrv.apps.crm.permissions import APICRMPermission
from rspsrv.apps.crm.services.v3.product_service import ProductService
from rspsrv.apps.crm.services.v3.trunk_service import TrunkService
from rspsrv.apps.package.versions.v1_0.services.package import PackageService
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.versions.v1.serializers.subscription import (
    SubscriptionSerializer,
)
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper


class BaseCrmAPIView(APIView):
    permission_classes = (APICRMPermission,)


class ProductAPIView(BaseCrmAPIView):
    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.GET_PRODUCT,
    )
    def get(self, request, subscription_code, *args, **kwargs):
        queryset = Subscription.objects.filter(subscription_code=subscription_code)

        if not queryset.exists():
            return response(
                request,
                error=_(
                    'Product with sub-id <{pid}> not found!'.format(
                        pid=subscription_code
                    )
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        elif queryset.count() > 1:
            return response(
                request,
                error=_('Product with sub-id <{pid}> not found!'.format(
                    pid=subscription_code)),
                status=status.HTTP_404_NOT_FOUND
            )

        serialized_data = SubscriptionSerializer(queryset, many=True).data

        return response(
            request,
            data=(serialized_data, None)
        )

    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.CREATE_PRODUCT,
    )
    def post(self, request, *args, **kwargs):
        try:
            result = TrunkService.create(request.data)
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail
            )

        return response(
            request,
            data=result,
            status=201
        )

    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.UPDATE_PRODUCT,
    )
    def put(self, request, subscription_code, *args, **kwargs):
        try:
            subscription_obj = ProductService.update_product(
                request.data,
                subscription_code
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail
            )

        serialized_data = SubscriptionSerializer(subscription_obj).data

        return response(
            request,
            data=serialized_data
        )


class ProductActivationAPIView(BaseCrmAPIView):
    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.PRODUCT_ACTIVATION,
    )
    def post(self, request, subscription_code, *args, **kwargs):
        try:
            subscription_obj = ProductService.change_product_activation(
                subscription_code=subscription_code,
                params=request.data,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail
            )

        serialized_data = SubscriptionSerializer(subscription_obj).data

        return response(
            request,
            data=serialized_data
        )


class ProductActivateProAPIView(BaseCrmAPIView):
    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.ACTIVATE_HOSTED,
    )
    def post(self, request, subscription_code, *args, **kwargs):
        try:
            ProductService.activate_pro(
                subscription_code=subscription_code,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail
            )

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class ProductDeallocationAPIView(BaseCrmAPIView):
    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.DEALLOCATE_PRODUCT,
    )
    def post(self, request, subscription_code, *args, **kwargs):
        try:
            data = ProductService.deallocate_product(
                subscription_code=subscription_code,
                body=request.body,
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(
            request,
            data=data,
            status=status.HTTP_200_OK,
        )


class ProductConvertAPIView(BaseCrmAPIView):
    @log_api_request(
        app_name=CrmConfig.name,
        label=CrmConfigurations.APILabels.CONVERT_PRODUCT,
    )
    def post(self, request, subscription_code, *args, **kwargs):
        try:
            subscription_obj = ProductService.convert_product(
                subscription_code=subscription_code,
                body=request.body
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        serialized_data = SubscriptionSerializer(subscription_obj).data

        return response(
            request,
            data=serialized_data
        )


class PackagesAPIView(BaseCrmAPIView):
    def get(self, request, *args, **kwargs):
        try:
            # Only finance should see not active or enable packages
            query_dict = dict(request.query_params)
            query_dict['is_active'] = [1]
            query_dict['is_enable'] = [1]
            packages_cgg = PackageService.get_packages(
                query_params=query_dict,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        response_kwargs = Helper.get_response_kwargs(
            packages_cgg,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(packages_cgg['data'], None),
            **response_kwargs,
        )
