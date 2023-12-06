from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.siam.permissions import ApiTokenPermission
from rspsrv.apps.siam.versions.v1.helpers.date_time_helper import DateTimeHelper
from rspsrv.apps.siam.versions.v1.serializers.numbering_capacity_serializer import NumberingCapacitySerializer
from rspsrv.apps.siam.apps import SiamConfig
from rspsrv.apps.siam.models import NumberingCapacity
from rspsrv.apps.siam.versions.v1.config import SIAMConfigurations
from rspsrv.tools.response import response_ok, response404


class NumberingCapacityAPIView(APIView):
    permission_classes = (ApiTokenPermission,)

    @log_api_request(
        app_name=SiamConfig.name,
        label=SIAMConfigurations.APILabels.GET_NUMBERING_CAPACITY,
    )
    def get(self, request, *args, **kwargs):
        from_date = request.GET.get('from_date', None)
        to_date = request.GET.get('to_date', None)

        gr_from_date = DateTimeHelper.to_object(
            from_date + " 00:00",
            to_gregorian=True,
        ) if from_date is not None else from_date
        gr_to_date = DateTimeHelper.to_object(
            to_date + " 23:59",
            to_gregorian=True,
        ) if to_date is not None else to_date

        try:
            queryset = NumberingCapacity.objects.filter(odate__range=(gr_from_date.date(), gr_to_date.date()))\
                .order_by('-odate')
        except NumberingCapacity.DoesNotExist:
            return response404(request)
        serializer = NumberingCapacitySerializer(
            queryset,
            many=True,
        )

        response_data = (serializer.data, None)

        return response_ok(request, data=response_data)
