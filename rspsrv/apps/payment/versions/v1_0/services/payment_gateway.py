# --------------------------------------------------------------------------
# Works with payment contracts and etc
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - payment_gateway.py
# Created at 2020-10-27,  14:10:34
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import importlib
import logging

from rest_framework import exceptions

from rspsrv.apps.payment.versions.v1_0.config.config import (
    PaymentConfiguration,
)

logger = logging.getLogger("common")
CGG_URLS = PaymentConfiguration.URLs


class PaymentGatewayService:
    user = None
    gateway_instance = None

    def __init__(self, gateway, app, user, related_name):
        """

        :param gateway:
        :param app:
        :param user:
        :param related_name:
        """
        self.user = user

        self.instantiate_gateway(gateway, app, related_name)

    @property
    def gateway(self):
        if not self.gateway_instance:
            raise AttributeError('Subscription instance not instantiated yet.')

        return self.gateway_instance

    def instantiate_gateway(self, gateway, app, related_name):
        """
        Make an Instance Dynamically from Available Gateways.
        :param related_name:
        :param app:
        :param gateway:
        :return:
        """

        try:
            gateway_module = importlib.import_module(
                'rspsrv.apps.payment.gateways.{}'.format(gateway)
            )
        except ImportError as exception:
            logger.error(exception)

            raise exceptions.ValidationError(
                detail='Subscription <{}> is not valid!'.format(gateway)
            )

        self.gateway_instance = gateway_module.Gateway(
            user=self.user,
            app=app,
            related_name=related_name,
            gateway=gateway,
        )

    def get_gateway(self, gateway):
        return self.instantiate_gateway(gateway)

    def send(self, params):
        """
        Send Params to Subscription API to Create New Transaction
        (It's First Step as usual).
        :return:
        """
        return self.gateway.send(params)

    def verify(self, params):
        """

        :param params:
        :return:
        """
        return self.gateway.verify(params)
