import logging

from django.db.models import Q
from django.utils.translation import gettext as _

from rspsrv.apps.cdr.models import CDR
from rspsrv.apps.siam.versions.v1 import config
from rspsrv.apps.siam.versions.v1.helpers.date_time_helper import (
    DateTimeHelper
)
from rspsrv.apps.siam.versions.v1.serializers.cdr_serializers import (
    CDRsResponseSerializer,
)
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class CDRService:
    @classmethod
    def get_cdrs(
            cls,
            number,
            direction,
            from_datetime,
            to_datetime,
    ):
        """
        Return CDRs Data.
        :param number:
        :param direction:
        :param from_datetime:
        :param to_datetime:
        :return:
        """
        try:
            to_datetime = DateTimeHelper.to_object(
                to_datetime,
                to_gregorian=True,
            )
        except api_exceptions.APIException:
            raise

        try:
            from_datetime = DateTimeHelper.to_object(
                from_datetime,
                to_gregorian=True,
            )
        except api_exceptions.APIException:
            raise

        if direction == config.CallDirection.IN_OUT_0:
            lookup = (
                    Q(caller__icontains=number) | Q(called__icontains=number)
            )
        elif direction == config.CallDirection.OUTBOUND_1:
            lookup = Q(caller__contains=number)
        elif direction == config.CallDirection.INBOUND_2:
            lookup = Q(called__contains=number)
        else:
            raise api_exceptions.ValidationError400(
                detail=_('Call flow value is not valid!'),
            )

        lookup = lookup & (
                Q(created_at__gte=from_datetime) &
                Q(created_at__lte=to_datetime)
        )

        cdrs_query = CDR.objects.filter(lookup)

        # Find Subscription.
        try:
            subscription_obj = Subscription.objects.get(
                number__icontains=number,
                activation=True,
            )
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                detail=_('Number not found!')
            )

        serializer_obj = CDRsResponseSerializer(
            cdrs_query,
            many=True,
            context={
                'number': subscription_obj.number,
                'lat': subscription_obj.latitude,
                'long': subscription_obj.longitude,
            }
        )

        return serializer_obj.data
