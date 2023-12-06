from django.urls import re_path

import rspsrv.apps.package.versions.v1_0.api as api

urls = [
    ############################################
    #       Package related URLs          #
    ############################################
    # All packages
    re_path(
        r'^(?:v1/)?packages[/]$',
        api.PackagesAPIView.as_view(),
        name='packages_get_post',
    ),
    # A single package
    re_path(
        r'^(?:v1/)?packages/(?P<package_id>[^/]+)[/]$',
        api.PackageAPIView.as_view(),
        name='package_get_path_delete',
    ),
]
