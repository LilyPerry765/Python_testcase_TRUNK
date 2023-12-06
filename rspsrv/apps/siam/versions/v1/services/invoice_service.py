import logging

from django.utils.translation import gettext as _
from jdatetime import datetime, timedelta

from rspsrv.apps.invoice.versions.v1_0.services.invoice import (
    InvoiceService as InvoiceAppService
)
from rspsrv.apps.siam.versions.v1.serializers.invoice_serializers import (
    InvoicesResponseSerializer,
)
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class InvoiceService:
    @classmethod
    def get_invoices(cls, number, from_datetime=None, to_datetime=None):
        """
        Return Invoices Data.
        :param number: 2191077070
        :param from_datetime: 1398/06/20 12:30
        :param to_datetime: 1398/06/20 12:30
        :return:
        """
        if to_datetime is None:
            to_datetime = datetime.now()
        else:
            try:
                to_datetime = datetime.strptime(
                    to_datetime,
                    '%Y/%m/%d %H:%M',
                )
            except ValueError:
                msg = _('DateTime string format is incorrect!')
                logger.error(msg)
                raise api_exceptions.ValidationError400(
                    detail=msg,
                )

        if from_datetime is None:
            from_datetime = to_datetime - timedelta(days=180)
        else:
            try:
                from_datetime = datetime.strptime(
                    from_datetime,
                    '%Y/%m/%d %H:%M',
                )
            except ValueError:
                msg = _('DateTime string format is incorrect!')
                logger.error(msg)
                raise api_exceptions.ValidationError400(
                    detail=msg,
                )
        from_datetime = from_datetime.togregorian().timestamp()
        to_datetime = to_datetime.togregorian().timestamp()

        try:
            subscription = Subscription.objects.get(
                number=number
            )
        except (Subscription.DoesNotExist, Subscription.MultipleObjectsReturned):
            raise api_exceptions.NotFound404(
                _('Subscription with this number does not exists')
            )
        query_params = {
            'created_at_from': from_datetime,
            'created_at_to': to_datetime,
        }
        try:
            cgg_invoice = InvoiceAppService.get_invoices(
                subscription_code=subscription.subscription_code,
                query_params=query_params,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)

        serializer_obj = InvoicesResponseSerializer(
            cgg_invoice['data'],
            many=True,
        )

        return serializer_obj.data
