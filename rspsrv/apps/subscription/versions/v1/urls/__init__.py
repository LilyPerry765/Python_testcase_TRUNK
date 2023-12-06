from django.urls import re_path

from rspsrv.apps.subscription.versions.v1 import api

urls = [
    # Subscription: Index.
    re_path(
        r'^(?:v1/)?subscriptions(?:/)?$',
        api.SubscriptionsAPIView.as_view(),
        name='Subscription_list'
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/subscriptions(?:/)?$',
        api.SubscriptionsExportAPIView.as_view(),
        name='export_subscriptions'
    ),
    # Subscription: Show, Update.
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)(?:/)?$',
        api.SubscriptionAPIView.as_view(),
        name='subscription'
    ),
    # Increase credit no pay mode
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)/assign(?:/)?$',
        api.SubscriptionAssignAPIView.as_view(),
        name='Subscription_assign'
    ),
    # Increase credit no pay mode
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)/auto-pay(?:/)?$',
        api.SubscriptionAutoPayAPIView.as_view(),
        name='Subscription_auto_pay'
    ),
    # Increase credit no pay mode
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)/credit(?:/)?$',
        api.SubscriptionCreditAPIView.as_view(),
        name='Subscription_credit'
    ),
    # Increase base balance no pay mode
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)/base-balance(?:/)?$',
        api.SubscriptionBaseBalanceAPIView.as_view(),
        name='Subscription_base_balance'
    ),
    # Debit balance no pay mode
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)/debit-balance('
        r'?:/)?$',
        api.SubscriptionDebitAPIView.as_view(),
        name='Subscription_debit_balance'
    ),
    # Add balance no pay mode
    re_path(
        r'^(?:v1/)?subscriptions/(?P<subscription_id>\d+)/add-balance(?:/)?$',
        api.SubscriptionAddBalanceAPIView.as_view(),
        name='Subscription_add_balance'
    ),
]
