from django.urls import re_path

from rspsrv.apps.crm.api.v3 import api as api_v3
from rspsrv.tools.deprecated_api import deprecated_api, removed_api

v3 = [
    re_path(
        r'^(?:v3/)?packages(?:/)?$',
        api_v3.PackagesAPIView.as_view(),
    ),
    re_path(
        r'^(?:v3/)?products(?:/)?$',
        api_v3.ProductAPIView.as_view(),
    ),
    re_path(
        r'^(?:v3/)?products/(?P<subscription_code>[\w-]+)(?:/)?$',
        api_v3.ProductAPIView.as_view(),
    ),
    re_path(
        r'^(?:v3/)?products/(?P<subscription_code>[\w-]+)/deallocate(?:/)?$',
        api_v3.ProductDeallocationAPIView.as_view(),
    ),
    re_path(
        r'^(?:v3/)?products/(?P<subscription_code>[\w-]+)/convert(?:/)?$',
        api_v3.ProductConvertAPIView.as_view(),
    ),
    re_path(
        r'^(?:v3/)?products/(?P<subscription_code>[\w-]+)/empower(?:/)?$',
        api_v3.ProductActivationAPIView.as_view(),
    ),
    re_path(
        r'^(?:v3/)?products/(?P<subscription_code>[\w-]+)/activate-pro(?:/)?$',
        api_v3.ProductActivateProAPIView.as_view(),
    ),
]
# Deprecated (@TODO: Remove this in version 4: Use removed_api)
v2 = [
    re_path(
        r'^v2/products(?:/)?$',
        deprecated_api,
    ),
    re_path(
        r'^v2/products/(?P<subscription_code>[\w-]+)(?:/)?$',
        deprecated_api,
    ),
    re_path(
        r'^v2/products/(?P<subscription_code>[\w-]+)/empower(?:/)?$',
        deprecated_api,
    ),
    re_path(
        r'^v2/products/(?P<subscription_code>[\w-]+)/deallocate(?:/)?$',
        deprecated_api,
    ),
    re_path(
        r'^v2/products/(?P<subscription_code>[\w-]+)/convert(?:/)?$',
        deprecated_api,
    ),
]
# Removed APIs
v1 = [
    re_path(
        r'^v1/product[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/product/(?P<gateway_number>\d+)[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/product/activation/(?P<gateway_number>\d+)[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/client[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/client/(?P<client_id>\d+)[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/client/(?P<client_id>\d+)/products[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/client/(?P<client_id>\d+)/products/(?P<gateway_number>\d+)[/]?$',
        removed_api,
    ),
    re_path(
        r'^v1/provinces(?:/)?$',
        removed_api,
    ),
    re_path(
        r'^v1/provinces/(?P<province_id>\d+)(?:/)?$',
        removed_api,
    ),
    re_path(
        r'^v1/cities(?:/)?$',
        removed_api,
    ),
    re_path(
        r'^v1/cities/(?P<city_id>\d+)(?:/)?$',
        removed_api,
    ),
]

urlpatterns = v3 + v2 + v1
