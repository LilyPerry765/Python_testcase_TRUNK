import logging

from django.shortcuts import redirect
from rest_framework.views import View

from rspsrv.apps.payment.versions.v1_0.services.payment_gateway import (
    PaymentGatewayService
)
from rspsrv.tools import response

logger = logging.getLogger("common")


class VerifyView(View):
    def post(self, request):
        """
        Get Transaction Data from Callee (Subscription Side), Verify It and Redirect to The Front Page.
        :param request:
        :return:
        """
        try:
            params = dict()

            params.update(**request.POST.dict())
            params.update(**request.GET.dict())

            payment_gateway_service = PaymentGatewayService(
                gateway=params.get('gateway'),
                app=params.get('app'),
                related_name=params.get('related_name'),
                user=request.user,
            )

            result = payment_gateway_service.verify(params)

            return redirect(result['redirect_to'])
        except AttributeError as exception:
            logger.error(exception)

            return response.response400(request, error=exception)
        except Exception as exception:
            logger.error(exception)

            return response.response500(request)

    def get(self, request, *args, **kwargs):
        """
        Redirect Step for MIS Payment Subscription.
        It Passes 'token' as a Query Parameter.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        params = request.GET.dict()

        payment_gateway_service = PaymentGatewayService(
            gateway=params.get('gateway'),
            app=params.get('app'),
            related_name=params.get('related_name'),
            user=request.user,
        )

        result = payment_gateway_service.verify(params)

        return redirect(result['redirect_to'])
