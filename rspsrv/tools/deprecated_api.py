from rest_framework.decorators import api_view, permission_classes

from rspsrv.tools.response import response_deprecated, response_removed


@api_view(['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'])
@permission_classes([])
def deprecated_api(request):
    return response_deprecated(request)


@api_view(['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'])
@permission_classes([])
def removed_api(request):
    return response_removed(request)
