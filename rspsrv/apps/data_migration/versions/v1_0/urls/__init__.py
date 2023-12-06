from django.urls import re_path

from rspsrv.apps.data_migration.versions.v1_0 import api

urls = [
    re_path(
        r'^cdr/cdrs/',
        api.CdrAPIView.as_view(),
        name='cdr',
    ),
    re_path(
        r'^extension/extensions/',
        api.ExtensionsAPIViews.as_view(),
        name='extensions',
    ),
    re_path(
        r'^extension/extension-numbers/',
        api.ExtensionNumbersAPIViews.as_view(),
        name='extension_numbers',
    ),
    re_path(
        r'^subscription/subscriptions/',
        api.SubscriptionAPIView.as_view(),
        name='subscriptions',
    ),
    re_path(
        r'^invoice/invoices/',
        api.InvoiceAPIView.as_view(),
        name='invoices',
    ),
    re_path(
        r'^notify/',
        api.NotifyAPIView.as_view(),
        name='notify',
    ),
]
