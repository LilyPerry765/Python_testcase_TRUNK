from django.urls import re_path

from rspsrv.apps.invoice.versions.v1_0.api import api

urls = [
    # Upload a file
    re_path(
        r'^(?:v1/)?upload[/]?$',
        api.UploadAPIView.as_view(),
        name='upload_bill',
    ),
    # Get all invoices
    re_path(
        r'^(?:v1/)?invoices[/]?$',
        api.InvoicesAPIView.as_view(),
        name='invoices',
    ),
    # Export all invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/invoices[/]?$',
        api.ExportInvoicesAPIView.as_view(),
        name='export_invoices',
    ),
    # Download a pdf version of a single invoice
    re_path(
        r'^(?:v1/)?invoices/(?P<invoice_id>[^/]+)/download[/]$',
        api.InvoiceDownloadAPIView.as_view(),
        name='invoice_download_pdf',
    ),
    # Get a single invoice
    re_path(
        r'^(?:v1/)?invoices/(?P<invoice_id>[^/]+)[/]$',
        api.InvoiceAPIView.as_view(),
        name='invoice',
    ),
    # All base balance invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/base-balance-invoices[/]$',
        api.ExportBaseBalanceInvoicesAPIView.as_view(),
        name='export_base_balance_invoices',
    ),
    # Export base balance invoices
    re_path(
        r'^(?:v1/)?base-balance-invoices[/]$',
        api.BaseBalanceInvoicesAPIView.as_view(),
        name='base_balance_invoices',
    ),
    # A single base balance invoice
    re_path(
        r'^(?:v1/)?base-balance-invoices/(?P<base_balance_invoice_id>[^/]+)['
        r'/]$',
        api.BaseBalanceInvoiceAPIView.as_view(),
        name='base_balance_invoice',
    ),
    # All credit invoices
    re_path(
        r'^(?:v1/)?credit-invoices[/]$',
        api.CreditInvoicesAPIView.as_view(),
        name='credit_invoices',
    ),
    # Export credit invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/credit-invoices[/]$',
        api.ExportCreditInvoicesAPIView.as_view(),
        name='export_credit_invoices',
    ),
    # A single credit invoice
    re_path(
        r'^(?:v1/)?credit-invoices/(?P<credit_invoice_id>[^/]+)[/]$',
        api.CreditInvoiceAPIView.as_view(),
        name='credit_invoice',
    ),
    # Download the pdf of a single credit invoice
    re_path(
        r'^(?:v1/)?credit-invoices/(?P<credit_invoice_id>[^/]+)/download[/]$',
        api.CreditInvoiceDownloadAPIView.as_view(),
        name='credit_invoice_download',
    ),
    # All package invoices
    re_path(
        r'^(?:v1/)?package-invoices[/]$',
        api.PackageInvoicesAPIView.as_view(),
        name='package_invoices_get_post',
    ),
    # Export package invoices
    re_path(
        r'^(?:v1/)?export/(?P<export_type>[^/]+)/package-invoices[/]$',
        api.ExportPackageInvoicesAPIView.as_view(),
        name='export_package_invoices',
    ),
    # A single package invoice
    re_path(
        r'^(?:v1/)?package-invoices/(?P<package_invoice_id>[^/]+)[/]$',
        api.PackageInvoiceAPIView.as_view(),
        name='package_invoice_get_patch',
    ),
]
