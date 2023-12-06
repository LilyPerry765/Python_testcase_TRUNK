from django.urls import re_path

from rspsrv.apps.cdr.api import api, api_operators

urlpatterns = [
    # get data
    re_path(
        r'^[/]?$',
        api.CDRAPIView.as_view(),
        name='cdr_list'
    ),
    re_path(
        r'^(?P<cdr_id>\d+)[/]?$',
        api.CDRAPIView.as_view(),
        name='cdr'
    ),

    # download recorded cdr
    re_path(
        r'^(?P<cdr_id>\d+)/download/(?P<token>.+)[/]?$',
        api.RecordedAudioDownloadAPIView.as_view(),
        name='recorded_audio_download_signed'
    ),
    # export cdrs
    re_path(
        r'^export/csv[/]?$',
        api.ExportCDRToCSVAPIView.as_view(),
        name='cdr_list_csv_export'
    ),
    re_path(
        r'^(?P<cdr_id>\d+)/export/csv[/]?$',
        api.ExportCDRToCSVAPIView.as_view(),
        name='cdr_csv_export'
    ),
    re_path(
        r'^user/calllog[/]?$',
        api.UserCallLogAPIView.as_view(),
        name='user_call_log'
    ),
    re_path(
        r'^call_minutes/',
        api.GetCallMinutes.as_view(),
        name='get_call_minutes'
    ),
    # get cdr based on operators
    re_path(
        r'^operator/(?P<operator>\d+)/cdr[/]?$',
        api_operators.OperatorCDRAPIView.as_view(),
        name='operator_cdr_list'
    ),
    re_path(
        r'^operator/(?P<operator>\d+)/cdr/export/csv$',
        api_operators.OperatorExportCSVCDRAPIView.as_view(),
        name='operator_cdr_csv'
    )
]
