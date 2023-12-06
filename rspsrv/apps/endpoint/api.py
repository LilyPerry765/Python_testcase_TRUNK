import json
import logging

from django.db.models import Q
from django.http import QueryDict
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.endpoint.apps import EndpointConfig
from rspsrv.apps.endpoint.config import EndpointConfigurations
from rspsrv.apps.endpoint.forms import EndpointModelForm
from rspsrv.apps.endpoint.models import Brand, Endpoint
from rspsrv.tools.permissions import (
    Group,
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

logger = logging.getLogger("common")


class BaseEndpointAPIView(APIView):
    permission_classes = [
        IsSupport |
        IsCustomerAdmin |
        IsCustomerOperator
    ]


class BrandAPIView(BaseEndpointAPIView):
    def get(self, request, brand_id=None):
        lookup = {}
        is_list = True

        if brand_id:
            lookup.update({'id': brand_id})
            is_list = False

        try:
            queryset = Brand.objects.filter(**lookup)
            data = Brand.serialize(queryset=queryset, request=request,
                                   is_list=is_list)
        except Brand.DoesNotExist:
            return response404(request)
        except Exception as any_exception:
            logger.error("Exception: {}".format(any_exception))

            return response500(request)

        return response_ok(request, data=data)


class BrandOptionAPIView(BaseEndpointAPIView):
    def get(self, request, brand_id):
        # noinspection PyBroadException
        try:
            brand = Brand.objects.get(id=brand_id)
            f = open(brand.template.path, 'r')
            template = f.read()
            f.close()

            template = json.loads(template)
            options = template['options']

            return response_ok(request, data=options)

        except Brand.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class EndpointAPIView(BaseEndpointAPIView):
    def get(self, request, endpoint_id=None):
        lookup = {}
        subscription_id = request.GET.get('subscription_id', None)
        if subscription_id and subscription_id != '':
            lookup.update({'subscription_id': subscription_id})
        is_list = True

        if request.user.groups.filter(
                Q(name=Group.CUSTOMER_ADMIN) | Q(name=Group.CUSTOMER_OPERATOR)
        ).exists():
            lookup.update({'subscription__customer': request.user.customer})

        if endpoint_id:
            lookup.update({'id': endpoint_id})
            is_list = False

        q_objects = Helper.generate_lookup(
            {
                'brand__name': 'brand__name__icontains',
                'mac_address': 'mac_address__icontains',
                'number': 'subscription__number_icontains',
            },
            self.request.query_params,
            q_objects=True
        )

        try:
            queryset = Endpoint.objects.filter(**lookup)
            if q_objects:
                queryset = queryset.filter(q_objects)
            data = Endpoint.serialize(queryset=queryset, request=request,
                                      is_list=is_list)
        except Endpoint.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error('Exception: %s', e)
            return response500(request)
        else:
            return response_ok(request, data=data)

    @log_api_request(
        app_name=EndpointConfig.name,
        label=EndpointConfigurations.APILabels.CREATE_ENDPOINT
    )
    def post(self, request):
        try:
            params = QueryDict(mutable=True)
            json_params = json.loads(request.body.decode('utf-8'))
            params.update(json_params)
            form = EndpointModelForm(params)

            if not form.is_valid():
                return response400(request, error=form.error_list)

            new_endpoint = form.save()
        except Exception as e:
            logger.error('Exception: %s', e)
            return response500(request)
        else:
            data = {'id': new_endpoint.id}

            return response_ok(request, data=data)

    @log_api_request(
        app_name=EndpointConfig.name,
        label=EndpointConfigurations.APILabels.DELETE_ENDPOINT
    )
    def delete(self, request, endpoint_id):
        try:
            Endpoint.objects.filter(id=endpoint_id).delete()
        except Exception as e:
            logger.error('Exception: %s', e)
            return response500(request)
        else:
            return response_ok(request)

    @log_api_request(
        app_name=EndpointConfig.name,
        label=EndpointConfigurations.APILabels.UPDATE_ENDPOINT
    )
    def put(self, request, endpoint_id):
        try:
            endpoint = Endpoint.objects.get(id=endpoint_id)

            params = QueryDict(mutable=True)
            json_params = json.loads(request.body.decode('utf-8'))
            params.update(json_params)
            form = EndpointModelForm(params, instance=endpoint)
        except Endpoint.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error('Exception: %s', e)

            return response500(request)
        else:
            if not form.is_valid():
                return response400(request, error=form.error_list)

            form.save()

            return response_ok(request)


class EnableEndpointAPIView(BaseEndpointAPIView):
    @log_api_request(
        app_name=EndpointConfig.name,
        label=EndpointConfigurations.APILabels.ENABLE_ENDPOINT
    )
    def put(self, request, endpoint_id):
        try:
            endpoint = Endpoint.objects.get(id=endpoint_id)
            endpoint.enabled = True
            endpoint.save()
        except Endpoint.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error('Exception: %s', e)
            return response500(request)
        else:
            return response_ok(request)

    @log_api_request(
        app_name=EndpointConfig.name,
        label=EndpointConfigurations.APILabels.DISABLE_ENDPOINT
    )
    def delete(self, request, endpoint_id):
        try:
            endpoint = Endpoint.objects.get(id=endpoint_id)
            endpoint.enabled = False
            endpoint.save()
        except Endpoint.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error('Exception: %s', e)
            return response500(request)
        else:
            return response_ok(request)
