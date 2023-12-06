from django.urls import re_path

from rspsrv.apps.payment.versions.v1_0.api import api

urls = [
    re_path(
        r'^(?:v1/)?payments[/]?$',
        api.PaymentsAPIView.as_view(),
        name='payments'
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/payments[/]?$',
        api.ExportPaymentsAPIView.as_view(),
        name='export_payments'
    ),
    re_path(
        r'^(?:v1/)?payments/(?P<payment_id>[^/]+)(?:/)?$',
        api.PaymentAPIView.as_view(),
        name='payment_get_patch',
    ),
    re_path(
        r'^(?:v1/)?payments/(?P<payment_id>[^/]+)/approval(?:/)?$',
        api.PaymentApprovalAPIView.as_view(),
        name='payment_approval',
    ),
    # A single package invoice
    re_path(
        r'^(?:v1/)?package-invoices/(?P<package_invoice_id>[^/]+)[/]$',
        api.PackageInvoicePaymentsAPIView.as_view(),
        name='package_invoice_payments',
    ),
    # A single credit invoice payments
    re_path(
        r'^(?:v1/)?credit-invoices/(?P<credit_invoice_id>[^/]+)[/]$',
        api.CreditInvoicePaymentsAPIView.as_view(),
        name='credit_invoice_payments',
    ),
    # A single base balance invoice payments
    re_path(
        r'^(?:v1/)?base-balance-invoices/(?P<base_balance_invoice_id>[^/]+)['
        r'/]$',
        api.BaseBalanceInvoicePaymentsAPIView.as_view(),
        name='base_balance_invoice_payments',
    ),
    # Get a single invoice
    re_path(
        r'^(?:v1/)?invoices/(?P<invoice_id>[^/]+)[/]$',
        api.InvoicePaymentsAPIView.as_view(),
        name='invoice_payments',
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/credit-invoices/('
        r'?P<credit_invoice_id>[^/]+)[/]$',
        api.ExportCreditInvoicePaymentsAPIView.as_view(),
        name='export_credit_payments',
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/package-invoices/('
        r'?P<package_invoice_id>[^/]+)[/]$',
        api.ExportPackageInvoicePaymentsAPIView.as_view(),
        name='export_package_invoice_payments',
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/invoices/(?P<invoice_id>['
        r'^/]+)[/]$',
        api.ExportInvoicePaymentsAPIView.as_view(),
        name='export_invoice_payments',
    ),
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/base-balance-invoices/('
        r'?P<base_balance_invoice_id>[^/]+)[/]$',
        api.ExportBaseBalanceInvoicePaymentsAPIView.as_view(),
        name='export_base_balance_invoice_payments',
    ),
]
