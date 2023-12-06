from django.urls import re_path

from rspsrv.apps.siam.versions.v1.api import trunk_api, cdr_api, invoice_api, numbering_capacity_api

urls = [
    re_path(
        r'^(v1/)?products/(?P<number>[^/]+)(?:/)?$',
        trunk_api.ProductAPIView.as_view(),
        name='product'
    ),
    re_path(
        r'^(v1/)?products/(?P<number>[^/]+)/suspend(?:/)?$',
        trunk_api.ProductSuspendAPIView.as_view(),
        name='product_suspend',
    ),
    re_path(
        r'^(v1/)?products/forward-settings(?:/)?$',
        trunk_api.ProductForwardSettingsAPIView.as_view(),
        name='product_forward_settings',
    ),
    re_path(
        r'^(v1/)?products/(?P<number>[^/]+)/invoices(?:/)?$',
        invoice_api.ProductInvoicesAPIView.as_view(),
        name='product_invoices',
    ),
    re_path(
        r'^(v1/)?products/(?P<number>[^/]+)/cdrs(?:/)?$',
        cdr_api.CDRsAPIView.as_view(),
        name='product_cdrs',
    ),
    re_path(
        r'^(v1/)?numbering_capacity(?:/)?$',
        numbering_capacity_api.NumberingCapacityAPIView.as_view(),
        name='numbering_capacity',
    ),
]
