from django.urls import re_path

from .api import (
    BrandAPIView,
    BrandOptionAPIView,
    EndpointAPIView,
    EnableEndpointAPIView,
)

urlpatterns = [
    # Brand: Index.
    re_path(r'brand[/]?$', BrandAPIView.as_view(), name='brand_list'),
    # Brand: Show.
    re_path(r'brand/(?P<brand_id>\d+)[/]?$', BrandAPIView.as_view(),
            name='brand'),
    #
    re_path(r'brand/(?P<brand_id>\d+)/options[/]?$',
            BrandOptionAPIView.as_view(), name='options'),
    # Endpoint: Index, Store.
    re_path(r'endpoint[/]?$', EndpointAPIView.as_view(), name='endpoint_list'),
    # Endpoint: Show, Update, Delete.
    re_path(r'endpoint/(?P<endpoint_id>\d+)[/]?$', EndpointAPIView.as_view(),
            name='endpoint'),
    # Endpoint: Enable.
    re_path(r'endpoint/(?P<endpoint_id>\d+)/enable[/]?$',
            EnableEndpointAPIView.as_view(), name='enable'),
]
