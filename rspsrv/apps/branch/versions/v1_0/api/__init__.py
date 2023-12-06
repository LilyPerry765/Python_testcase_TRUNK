from django.utils.translation import gettext as _
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.branch.apps import BranchConfig
from rspsrv.apps.branch.versions.v1_0.config import BranchConfiguration
from rspsrv.apps.branch.versions.v1_0.services.branch import (
    BranchService,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.permissions import (
    IsSuperUser,
)
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper


class BranchesAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = BranchService.get_branches(
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
        app_name=BranchConfig.name,
        label=BranchConfiguration.APILabels.CREATE_BRANCH,
    )
    def post(
            self,
            request,
            *args,
            **kwargs
    ):
        try:
            response_data = BranchService.add_branch(
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Add branch'),
        )


class BranchAPIView(APIView):
    permission_classes = (IsSuperUser,)

    def get(
            self,
            request,
            branch,
            *args,
            **kwargs
    ):
        try:
            response_data = BranchService.get_branch(
                branch,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Branch'),
        )

    @log_api_request(
        app_name=BranchConfig.name,
        label=BranchConfiguration.APILabels.UPDATE_BRANCH,
    )
    def patch(
            self,
            request,
            branch,
            *args,
            **kwargs
    ):
        try:
            response_data = BranchService.update_branch(
                branch,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Update branch'),
        )

    @log_api_request(
        app_name=BranchConfig.name,
        label=BranchConfiguration.APILabels.DELETE_BRANCH,
    )
    def delete(
            self,
            request,
            branch,
            *args,
            **kwargs
    ):
        try:
            response_data = BranchService.delete_branch(
                branch,
            )
        except api_exceptions.APIException as e:
            return response(request, error=e.detail, status=e.status_code)

        return response(
            request,
            status=response_data["status"],
            data=response_data["data"],
            message=_('Remove branch'),
        )
