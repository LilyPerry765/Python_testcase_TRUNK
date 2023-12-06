from django.urls import re_path

import rspsrv.apps.ocs.versions.v1_0.api as api

urls = [
    ############################################
    #       Notification related URLs          #
    ############################################
    re_path(
        r'^(?:v1/)?notify/interim-invoice-auto-payed(?:/)?$',
        api.AutoPayInterimInvoice.as_view(),
        name='interim_invoice_auto_payed'
    ),
    re_path(
        r'^(?:v1/)?notify/periodic-invoice(?:/)?$',
        api.PeriodicInvoicesAPIView.as_view(),
        name='periodic_invoice'
    ),
    re_path(
        r'^(?:v1/)?notify/interim-invoice(?:/)?$',
        api.InterimInvoicesAPIView.as_view(),
        name='interim_invoice'
    ),
    re_path(
        r'^(?:v1/)?notify/postpaid-max-usage(?:/)?$',
        api.PostpaidMaxUsageAPIView.as_view(),
        name='postpaid_max_usage'
    ),
    re_path(
        r'^(?:v1/)?notify/due-date/(?P<warning_type>[^/]+)(?:/)?$',
        api.OverdueAPIView.as_view(),
        name='overdue'
    ),
    re_path(
        r'^(?:v1/)?notify/prepaid-expired(?:/)?$',
        api.PrepaidExpiredAPIView.as_view(),
        name='prepaid_expired'
    ),
    re_path(
        r'^(?:v1/)?notify/prepaid-renewed(?:/)?$',
        api.PrepaidRenewedAPIView.as_view(),
        name='prepaid_renewed'
    ),
    re_path(
        r'^(?:v1/)?notify/prepaid-eighty-percent(?:/)?$',
        api.EightyPercentPrepaidAPIView.as_view(),
        name='prepaid_eighty_percent'
    ),
    re_path(
        r'^(?:v1/)?notify/prepaid-max-usage(?:/)?$',
        api.MaxUsagePrepaidAPIView.as_view(),
        name='prepaid_max_usage'
    ),
    re_path(
        r'^(?:v1/)?notify/deallocation/(?P<warning_type>[^/]+)(?:/)?$',
        api.DeallocationAPIView.as_view(),
        name='deallocation'
    ),
    ############################################
    #       Destination related URLs           #
    ############################################
    re_path(
        r'^(?:v1/)?destinations(?:/)?$',
        api.DestinationsAPIView.as_view(),
        name='destinations'
    ),
    ############################################
    #       Configuration related URLs         #
    ############################################
    re_path(
        r'^(?:v1/)?runtime-configs(?:/)?$',
        api.RuntimeConfigAPIView.as_view(),
        name='runtime_config'
    ),
]
