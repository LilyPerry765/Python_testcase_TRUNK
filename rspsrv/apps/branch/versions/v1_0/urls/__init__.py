from django.urls import re_path

import rspsrv.apps.branch.versions.v1_0.api as api

urls = [
    ############################################
    #            Branch related URLs           #
    ############################################
    re_path(
        r'^(?:v1/)?branches(?:/)?$',
        api.BranchesAPIView.as_view(),
        name='branches'
    ),
    re_path(
        r'^(?:v1/)?branches/(?P<branch>[^/]+)(?:/)?$',
        api.BranchAPIView.as_view(),
        name='branch'
    ),
]
