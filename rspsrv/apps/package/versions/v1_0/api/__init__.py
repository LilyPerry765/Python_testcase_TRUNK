from django.utils.translation import gettext as _
from rest_framework import exceptions, status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.package.apps import PackageConfig
from rspsrv.apps.package.versions.v1_0.config import PackageConfiguration
from rspsrv.apps.package.versions.v1_0.services.package import PackageService
from rspsrv.tools import api_exceptions
from rspsrv.tools.permissions import (
    IsSuperUser,
    IsSupport,
    IsFinance,
    IsSales,
    IsCustomerAdmin,
    IsCustomerOperator,
)
from rspsrv.tools.permissions.base import CheckPermission
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper


class BaseAdminInvoiceAPIView(APIView):
    permission_classes = [
        IsSuperUser |
        IsSales |
        IsSupport |
        IsCustomerAdmin |
        IsCustomerOperator |
        IsFinance
    ]


class PackageAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, package_id=None):
        try:
            cgg_package = PackageService.get_package(
                package_id=package_id,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )
        return response(
            request,
            data=cgg_package['data']
        )

    @log_api_request(
        app_name=PackageConfig.name,
        label=PackageConfiguration.APILabels.UPDATE_PACKAGE
    )
    def patch(self, request, package_id=None):
        if not (CheckPermission.is_support(
                request) or CheckPermission.is_sales(request)):
            raise api_exceptions.PermissionDenied403(_(
                'Only sales and support can update packages'
            ))
        try:
            cgg_package = PackageService.update_package(
                package_id=package_id,
                payload=request.body,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(request, data=cgg_package['data'])

    @log_api_request(
        app_name=PackageConfig.name,
        label=PackageConfiguration.APILabels.DELETE_PACKAGE
    )
    def delete(self, request, package_id=None):
        if not (CheckPermission.is_support(
                request) or CheckPermission.is_sales(request)):
            raise api_exceptions.PermissionDenied403(_(
                'Only sales and support can delete packages'
            ))
        try:
            PackageService.delete_package(
                package_id=package_id,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(request, status=status.HTTP_204_NO_CONTENT)


class PackagesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request):
        if not (CheckPermission.is_support(
                request) or CheckPermission.is_sales(request)):
            try:
                # Only sales and support should see not active or enable
                # packages
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
        else:
            try:
                packages_cgg = PackageService.get_packages(
                    query_params=request.query_params,
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

    @log_api_request(
        app_name=PackageConfig.name,
        label=PackageConfiguration.APILabels.CREATE_PACKAGE
    )
    def post(self, request):
        if not (CheckPermission.is_support(
                request) or CheckPermission.is_sales(request)):
            raise api_exceptions.PermissionDenied403(_(
                'Only sales and support can add packages'
            ))
        try:
            cgg_package = PackageService.create_new_package(
                payload=request.body,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(request, data=cgg_package['data'])
