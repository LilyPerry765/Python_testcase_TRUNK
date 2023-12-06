import json
import logging
import math

import requests
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from requests import exceptions as requests_exceptions
from rest_framework import exceptions, status, request
from rest_framework import serializers
from rest_framework import status as http_status_codes

from rspsrv.apps.payment.contracts.gateway import GatewayContract
from rspsrv.apps.payment.versions.v1_0.services.payment import PaymentService
from rspsrv.tools import response

logger = logging.getLogger("common")


class ResponseSerializer(serializers.Serializer):
    payurl = serializers.CharField()
    orderid = serializers.CharField()
    tokencode = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class VerifyResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    amount = serializers.CharField(allow_blank=True)
    reference = serializers.CharField(allow_blank=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# noinspection PyBroadException
class Gateway(GatewayContract):
    config = None
    user = None
    app = None
    gateway = None

    def __init__(self, user, app, related_name, gateway):
        self.config = settings.APPS['payment']['gateways']['mis']
        self.user = user
        self.app = app
        self.related_name = related_name
        self.gateway = gateway

        GatewayContract.__init__(self, user, app, related_name, gateway)

    @transaction.atomic()
    def send(self, params):
        params['amount'] = math.ceil(params['amount'])
        payment_id = params['related_pay']['payment_id']
        generic_field = params.pop('generic_field')
        params.update({
            'redirecturl': self.get_post_back_url(
                gateway='mis',
                app=self.app,
                payment_id=payment_id,
                related_name=self.related_name,
                invoice_id=params['invoice_id']
            ),
            # This is to the hideous design of MIS payment API!
            'phonenumber': generic_field,
            'invoice': payment_id,
            'price': params['amount'],
        })

        try:
            api_response = requests.post(
                self.get_url(self.config['uris']['send']),
                params,
                headers={
                    'Authorization': self.config['api_key'],
                },
            )
        except requests_exceptions.RequestException as e:
            logger.error(
                "MIS Payment failed - "
                "URL: {} - Params: {} - Error: {}".format(
                    self.get_url(self.config['uris']['send']),
                    params,
                    str(e)
                )
            )
            raise exceptions.APIException(detail=str(e))

        if not status.is_success(api_response.status_code):
            logger.error(
                "MIS Payment failed - "
                "URL: {} - Params: {} - Error: {}".format(
                    self.get_url(self.config['uris']['send']),
                    params,
                    str(api_response.content)
                )
            )
            raise exceptions.APIException(
                detail=_('{code}: <{msg}>'.format(
                    code=api_response.status_code,
                    msg=api_response.content
                )
                ),
                code=api_response.status_code,
            )

        response_serializer = ResponseSerializer(data=api_response.json())

        try:
            response_serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError:
            raise

        return {
            'payment': params['related_pay'],
            'redirect_to': response_serializer.validated_data['payurl'],
        }

    @transaction.atomic()
    def verify(self, params):
        """
        Get Verification Result from Gateway for this Transaction.
        :param params:
        :return:
        """
        # receive MIS token
        api_response = requests.get(
            self.get_url(self.config['uris']['verify'].format(
                mis_token_code=params['token']
            )
            ),
            headers={
                'Authorization': self.config['api_key'],
            },
        )

        if not status.is_success(api_response.status_code):
            raise exceptions.APIException(
                detail=_(
                    '{code}: <{msg}>'.format(
                        code=api_response.status_code,
                        msg=api_response.content,
                    )
                ),
                code=api_response.status_code,
            )

        response_serializer = VerifyResponseSerializer(
            data=api_response.json()
        )

        if not response_serializer.is_valid():
            response.response500('request')

        status_code = False
        if response_serializer.validated_data['status'] == '0':
            status_code = True

        try:
            PaymentService.update_payment(
                payment_id=params['payment_id'],
                status_code=status_code,
                extra_data=response_serializer.validated_data,
            )
        except json.JSONDecodeError:
            return response.response(
                request,
                error='JSON is Not Valid',
                status=status.HTTP_400_BAD_REQUEST,
            )
        except exceptions.APIException as e:
            return response.response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        redirect_to = self.result_page_url(
            redirect_to=params['redirect_to'],
        )

        return response.pure(
            status=http_status_codes.HTTP_301_MOVED_PERMANENTLY,
            redirect_to=redirect_to
        )

    def gateway_url(self, **kwargs):
        internal_transaction_id = kwargs.pop('internal_transaction_id')

        return self.get_url(
            self.config['uris']['payment'].format(
                internal_transaction_id=internal_transaction_id
            )
        )

    def result_page_url(self, **kwargs):
        base_url = settings.DASHBOARD_REDIRECT_ABSOLUTE.strip('/')
        relative_url = settings.PAYMENT_REDIRECT_RELATIVE.strip('/')
        redirect_to = kwargs.pop('redirect_to')
        redirect_to = redirect_to.strip('/')

        return '{base_url}/{relative_url}/{redirect_to}'.format(
            base_url=base_url,
            relative_url=relative_url,
            redirect_to=redirect_to,
        )
