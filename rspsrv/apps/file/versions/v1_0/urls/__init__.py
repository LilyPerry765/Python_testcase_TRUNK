from django.urls import re_path

from rspsrv.apps.file.versions.v1_0 import api

urls = [
    re_path(
        r'^subscriptions/(?P<file_id>[^/]+)[/]$',
        api.FileAPIView.as_view(),
        name='file',
    ),
    re_path(
        r'^files/(?P<file_id>[^/]+)/download[/]$',
        api.DownloadFileAPIView.as_view(),
        name='file',
    ),
]
