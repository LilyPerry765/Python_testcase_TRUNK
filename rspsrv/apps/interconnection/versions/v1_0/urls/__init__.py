from django.urls import re_path

import rspsrv.apps.interconnection.versions.v1_0.api as api

urls = [
    ############################################
    #           Operator related URLs          #
    ############################################
    re_path(
        r'^(?:v1/)?operators(?:/)?$',
        api.OperatorsAPIView.as_view(),
        name='operators'
    ),
    re_path(
        r'^(?:v1/)?operators/(?P<operator>[^/]+)(?:/)?$',
        api.OperatorAPIView.as_view(),
        name='operator'
    ),
    ############################################
    #           Profit related URLs            #
    ############################################
    re_path(
        r'^(?:v1/)?profits(?:/)?$',
        api.ProfitsAPIView.as_view(),
        name='profits'
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/profits(?:/)?$',
        api.ExportProfitsAPIView.as_view(),
        name='export_profits'
    ),
    re_path(
        r'^(?:v1/)?profits/(?P<profit>[^/]+)(?:/)?$',
        api.ProfitAPIView.as_view(),
        name='profit'
    ),
    re_path(
        r'^(?:v1/)?profits/(?P<profit>[^/]+)/download(?:/)?$',
        api.DownloadProfitAPIView.as_view(),
        name='profit_download'
    ),
]
