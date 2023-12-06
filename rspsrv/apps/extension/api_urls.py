from django.urls import re_path

from rspsrv.apps.extension import api

urlpatterns = [
    # Extension: Index, Store.
    re_path(
        r'^extensions[/]?$',
        api.ExtensionAPIView.as_view(),
        name='extension_list'
    ),
    # Extension: Show, Update, Delete.
    re_path(
        r'^extensions/(?P<extension_id>\d+)[/]?$',
        api.ExtensionAPIView.as_view(),
        name='extension'
    ),
    re_path(
        r'^extensions/(?P<extension_id>\d+)/enable[/]?$',
        api.ExtensionEnablityAPIView.as_view(),
        name='enable_extension'
    ),
    re_path(
        r'^extensions/(?P<extension_id>\d+)/call_waiting[/]?$',
        api.ExtensionCallWaitingAPIView.as_view(),
        name='enable_extension_call_waiting'
    ),

    re_path(
        r'^extensions/(?P<extension_id>\d+)/webenable[/]?$',
        api.ExtensionWebEnablityAPIView.as_view(),
        name='extension_web_enable'
    ),

    re_path(
        r'^extensions/(?P<extension_id>\d+)/externalcall[/]?$',
        api.ExtensionExternalCallEnablityAPIView.as_view(),
        name='extension_external_call'
    ),
    re_path(
        r'^extensions/(?P<extension_id>\d+)/endpoint/(?P<endpoint_id>\d+)['
        r'/]?$',
        api.SetExtensionToEndpointAPIView.as_view(),
        name='set_endpoint_to_extension'),

    # Extension: Show, Update.
    re_path(r'extensions/(?P<extension_id>\d+)/status[/]?$',
            api.ExtensionStatus.as_view(), name='extension_status'),

    re_path(
        r'^route_numbers[/]$',
        api.ExtensionNumberByType.as_view(),
        name='extension_numbers_by_type'
    ),
]
