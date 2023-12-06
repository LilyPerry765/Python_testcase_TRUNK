import json
import logging

from django.db.models import Q
from django.http import QueryDict
from rest_framework.views import APIView

from rspsrv.apps.call.apps.base import CallApplicationType
from rspsrv.apps.endpoint.models import Endpoint
from rspsrv.apps.extension.forms import (
    ExtensionModelForm,
    ExtensionStatusForm,
)
from rspsrv.apps.extension.models import (
    Extension,
)
from rspsrv.tools.custom_paginator import CustomPaginator
from rspsrv.tools.permissions import (
    Group,
    IsSuperUser,
    IsSupport,
    IsCustomerAdmin,
    IsCustomerOperator,
)
from rspsrv.tools.response import (
    response_ok,
    response400,
    response500,
    response404,
)
from rspsrv.tools.utility import Helper
from .alt_serializers import ExtensionUpdateSerializer
from .apps import ExtensionConfig
from .config import ExtensionConfigurations
from .serilaizers import ExtensionNumberSerializer
from ..api_request.decorators import log_api_request
from ...tools import api_exceptions

logger = logging.getLogger("common")


class BaseExtensionAPIView(APIView):
    permission_classes = [
        IsSuperUser |
        IsSupport |
        IsCustomerAdmin |
        IsCustomerOperator
    ]


class SupportExtensionAPIView(APIView):
    permission_classes = [
        IsSuperUser |
        IsSupport
    ]


class ExtensionAPIView(BaseExtensionAPIView):
    def get(self, request, extension_id=None):
        lookup = {}
        is_list = True

        if request.user.groups.filter(
                Q(name=Group.CUSTOMER_ADMIN) | Q(name=Group.CUSTOMER_OPERATOR)
        ).exists():
            lookup.update({'customer': request.user.customer})

        if extension_id:
            lookup.update({'id': extension_id})
            is_list = False

        if "t" in request.query_params:
            query = request.query_params["t"]
            try:
                prime_code = int(
                    query,
                )
            except ValueError:
                prime_code = 0
            queryset = Extension.objects.filter(
                Q(extension_number__number__contains=query) |
                Q(endpoint__brand__name__icontains=query) |
                Q(callerid__contains=query) |
                Q(ring_seconds__contains=query) |
                Q(customer__id__icontains=prime_code)
            )
        else:
            filter_dict = {
                'number': 'extension_number__number__contains',
                'brand_name': 'endpoint__brand__name__icontains',
                'callerid': 'callerid__contains',
                'ring_seconds': 'ring_seconds__contains',
            }
            q_objects = Helper.generate_lookup(
                filter_dict,
                self.request.query_params,
                q_objects=True,
            )
            queryset = Extension.objects.filter(**lookup)
            if q_objects:
                queryset = queryset.filter(q_objects)

        try:
            queryset = Helper.order_by_query(
                Extension,
                queryset,
                request.query_params,
            )
            data = Extension.serialize(
                queryset=queryset,
                request=request,
                is_list=is_list,
            )
            return response_ok(request, data=data)
        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.CREATE_EXTENSION
    )
    def post(self, request):
        if request.user.groups.filter(
                Q(name=Group.SUPPORT_OPERATOR) | Q(name=Group.SUPPORT_ADMIN)
        ).exists():
            try:
                params = QueryDict(mutable=True)
                json_params = json.loads(request.body.decode('utf-8'))
                params.update(json_params)
                form = ExtensionModelForm(params)

                if not form.is_valid():
                    return response400(request, error=form.error_list)

                new_extension = form.save()
                data = {'id': new_extension.id}

                return response_ok(request, data=data)

            except Exception as e:
                logger.error("Exception: %s" % e)
                return response500(request)

        raise api_exceptions.PermissionDenied403()

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.UPDATE_EXTENSION_PASSWORD
    )
    def put(self, request, extension_id):
        try:
            if request.user.groups.filter(
                    Q(name=Group.CUSTOMER_ADMIN) |
                    Q(name=Group.CUSTOMER_OPERATOR)
            ).exists():
                extension = Extension.objects.get(
                    customer=request.user.customer,
                    id=extension_id
                )
            else:
                extension = Extension.objects.get(
                    id=extension_id
                )
            body = json.loads(request.body.decode('utf-8'))
            serializer = ExtensionUpdateSerializer(
                data=body,
            )
        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)
        else:
            if not serializer.is_valid():
                return response400(request, error=serializer.errors)
            # Update password of extension
            extension.password = serializer.data['password']
            extension.save()
            return response_ok(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.DELETE_EXTENSION
    )
    def delete(self, request, extension_id):
        try:
            if request.user.groups.filter(
                    Q(name=Group.SUPPORT_ADMIN) |
                    Q(name=Group.SUPPORT_OPERATOR)
            ).exists():
                extension = Extension.objects.get(
                    id=extension_id
                )
            else:
                extension = Extension.objects.get(
                    id=extension_id
                )
            extension.extension_number.delete()
            extension.delete()
            return response_ok(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class ExtensionEnablityAPIView(SupportExtensionAPIView):
    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.ENABLE_EXTENSION
    )
    def put(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.enabled = True
            extension.save()
            return response_ok(request)
        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.DISABLE_EXTENSION
    )
    def delete(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.enabled = False
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class ExtensionCallWaitingAPIView(SupportExtensionAPIView):
    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.ENABLE_CALL_WAITING
    )
    def put(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.call_waiting = True
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.DISABLE_CALL_WAITING
    )
    def delete(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.call_waiting = False
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class ExtensionWebEnablityAPIView(SupportExtensionAPIView):
    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.ENABLE_WEB_EXTENSION
    )
    def put(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.web_enabled = True
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.DISABLE_WEB_EXTENSION
    )
    def delete(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.web_enabled = False
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class ExtensionExternalCallEnablityAPIView(SupportExtensionAPIView):
    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.ENABLE_EXTERNAL_CALL
    )
    def put(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.external_call_enable = True
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.DISABLE_EXTERNAL_CALL
    )
    def delete(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.external_call_enable = False
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class SetExtensionToEndpointAPIView(SupportExtensionAPIView):
    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.SET_EXTENSION_TO_ENDPOINT
    )
    def post(self, request, extension_id, endpoint_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            endpoint = Endpoint.objects.get(id=endpoint_id)
            extension.endpoint = endpoint
            extension.save()
            return response_ok(request)
        except Extension.DoesNotExist:
            return response404(request)
        except Endpoint:
            return response400(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.UNSET_EXTENSION_TO_ENDPOINT
    )
    def delete(self, request, extension_id, endpoint_id=None):
        try:
            extension = Extension.objects.get(id=extension_id)
            extension.endpoint = None
            extension.save()

            return response_ok(request)

        except Extension.DoesNotExist:
            return response404(request)
        except Endpoint:
            return response400(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class ExtensionStatus(BaseExtensionAPIView):
    def get(self, request, extension_id):
        try:
            extension = Extension.objects.get(id=extension_id)
            data = {'status': extension.status}
            return response_ok(request, data=data)
        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)

    @log_api_request(
        app_name=ExtensionConfig.name,
        label=ExtensionConfigurations.APILabels.UPDATE_EXTENSION_STATUS
    )
    def put(self, request, extension_id):
        try:
            params = QueryDict(mutable=True)
            json_params = json.loads(request.body.decode('utf-8'))
            params.update(json_params)
            form = ExtensionStatusForm(params)
            if not form.is_valid():
                return response400(request, error=form.error_list)

            lookup = {'id': extension_id}

            if request.user.groups.filter(
                    Q(name=Group.CUSTOMER_ADMIN) | Q(
                        name=Group.CUSTOMER_OPERATOR)
            ).exists():
                lookup.update({'customer': request.user.customer})

            extension = Extension.objects.get(**lookup)
            extension.status = form.cleaned_data['status']
            extension.forward_to = form.cleaned_data['forward_to']
            extension.save()
            return response_ok(request)
        except Extension.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class ExtensionNumberByType(BaseExtensionAPIView):
    def get(self, request):
        route_type = request.GET.get('route_type', None)
        extension_numbers = []
        if route_type == CallApplicationType.EXTENSION:
            for extension in Extension.objects.all():
                extension_numbers.append(ExtensionNumberSerializer(
                    extension.extension_number).get_dict())

        response_data = CustomPaginator().paginate(
            request=request,
            data=extension_numbers,
        )

        return response_ok(request, response_data)
