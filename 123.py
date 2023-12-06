####################################################################################rspsrv/apps/gateway/api.py at end of file and import part
from .serilaizers import GatewaySerializerNew
from rest_framework.response import Response
----------------------------

class MainNumberAPIView(APIView):
    def get(self, request, main_number=None):
        lookup, is_list = ({}, True)
        if main_number:
            lookup, is_list = ({'main_number': main_number}, False)

        else:
            if (ProductType.is_personal() or ProductType.is_trunk()) and not request.user.is_superuser:
                try:
                    gateway = Gateway.objects.get(main_number=get_gateway_number(request.user.username))
                    lookup['id'] = gateway.id
                    is_list = True
                except (Gateway.DoesNotExist, Gateway.MultipleObjectsReturned):
                    return response403(request)
            else:
                is_list = True

        q_objects = Helper.generate_lookup(
            {
                'main_number': 'main_number__icontains',
                'destination_number': 'destination_number__icontains',
            },
            self.request.query_params,
            q_objects=True
        )

        try:
            queryset = Gateway.objects.filter(**lookup)

            if q_objects:
                queryset = queryset.filter(q_objects)

            data = Gateway.serialize(queryset=queryset, request=request, is_list=is_list)
        except Gateway.DoesNotExist:
            return response404(request)
        except Exception as e:
            logger.error("Exception: %s" % e)

            return response500(request)
        else:
            return response_ok(request, data=data)


class GetGatewayBaseOnMainNumberAPIView(APIView):
    """
    this api get gateway from Gateway model base on main number
    main_number is mandatory that is not passed fill by None
    """
    @staticmethod
    def get(request):
        print(request)
        if "main_number" not in request.keys():
            return Response({'detail': 'main number field is required'}, status.HTTP_400_BAD_REQUEST,)
        else:
            main_number = request["main_number"]
        try:
            gateway = Gateway.objects.get(main_number=main_number)
        except Gateway.DoesNotExist():
            return Response(status.HTTP_404_NOT_FOUND)
        serializer = GatewaySerializerNew(gateway, context={"request": request})
        return Response(serializer.data)
####################################################################################rspsrv/apps/gateway/api_urls.py before end of ] urlpatterns
    # get gateway base on base number.
    url(
        r'gateway/(?P<gateway-base-number>\d+)/$',
        api.MainNumberAPIView.as_view(),
        name='base_number_gateway',
    ),
    # get gateway base on base number new.
    url(
        r'gateway/(?P<gateway-detail>\d+)/$',
        api.GetGatewayBaseOnMainNumberAPIView.as_view(),
        name='detail_gateway',
    )
########################################################################################rspsrv/apps/gateway/serilaizers.py at end of file
class GatewaySerializerNew(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = '__all__'