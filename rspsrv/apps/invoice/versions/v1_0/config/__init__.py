from django.utils.translation import gettext_lazy as _
from model_utils import Choices


# Deprecated
class BillConfig:
    def __init__(self):
        pass

    STATE_CHOICES = Choices(
        (0, 'ready_to_pay', _('Ready to Pay')),
        (1, 'pending', _('Pending')),
        (2, 'paid', _('Paid')),
        (3, 'revoke', _('Revoke')),
    )

    INVOICE_TYPES = (
        (
            'invoice',
            'invoice',
        ),
        (
            'base_balance_invoice',
            'basebalanceinvoice'
        ),
    )


class InvoiceConfiguration:
    class InvoiceTypes:
        INVOICE = 'invoice'
        BASE_BALANCE_INVOICE = 'base_balance_invoice'
        CREDIT_INVOICE = 'credit_invoice'
        PACKAGE_INVOICE = 'package_invoice'

    class OperationTypes:
        INCREASE = 'increase'
        DECREASE = 'decrease'

    class URLs:
        EXPORT_INVOICES = 'api/finance/v1/export/{ex_type}/invoices/'
        EXPORT_INVOICES_WITH_SUBSCRIPTIONS = 'api/finance/v1/export/{' \
                                             'ex_type}/subscriptions/{' \
                                             'sid}/invoices/'
        EXPORT_INVOICES_WITH_CUSTOMER = 'api/finance/v1/export/{' \
                                        'ex_type}/customers/{' \
                                        'cid}/invoices/'
        EXPORT_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/invoices/'
        INVOICES = 'api/finance/v1/invoices/'
        INVOICES_WITH_SUBSCRIPTIONS = 'api/finance/v1/subscriptions/{' \
                                      'sid}/invoices/'
        INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{sid}/invoices/'
        INVOICES_WITH_CUSTOMER = \
            'api/finance/v1/customers/{cid}/invoices/'
        INVOICE = 'api/finance/v1/invoices/{iid}/'
        INVOICE_WITH_SUBSCRIPTIONS = 'api/finance/v1/subscriptions/{' \
                                     'sid}/invoices/{iid}/'
        INVOICE_WITH_CUSTOMERS = 'api/finance/v1/customers/{cid}/invoices/{' \
                                 'iid}/'
        INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{sid}/invoices/{' \
            'iid}/'
        INTERIM_INVOICE = 'api/finance/v1/subscriptions/{sid}/invoices/'
        BASE_BALANCE_INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/base-balance-invoices/{iid}/'
        BASE_BALANCE_INVOICE_WITH_CUSTOMER = 'api/finance/v1/customers/{' \
                                             'cid}/base-balance-invoices/{iid}'
        BASE_BALANCE_INVOICE_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/subscriptions/{sid}/base-balance-invoices/{iid}/'
        BASE_BALANCE_INVOICE = 'api/finance/v1/base-balance-invoices/{iid}/'
        BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/base-balance-invoices/'
        EXPORT_BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/base-balance-invoices/'
        BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/subscriptions/{sid}/base-balance-invoices/'
        EXPORT_BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/export/{ex_type}/subscriptions/{' \
            'sid}/base-balance-invoices/'
        EXPORT_BASE_BALANCE_INVOICES_WITH_CUSTOMERS = \
            'api/finance/v1/export/{ex_type}/customers/{' \
            'cid}/base-balance-invoices/'
        BASE_BALANCE_INVOICES = 'api/finance/v1/base-balance-invoices/'
        EXPORT_BASE_BALANCE_INVOICES = 'api/finance/v1/export/{' \
                                       'ex_type}/base-balance-invoices/'
        BASE_BALANCE_INVOICES_WITH_CUSTOMER = 'api/finance/v1/customers/{' \
                                              'cid}/base-balance-invoices/'
        PACKAGE_INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/package-invoices/{pid}/'
        MIGRATE_BASE_BALANCES = \
            'api/finance/v1/migration/base-balance-invoices/'
        MIGRATE_INVOICES = 'api/finance/v1/migration/invoices/'
        CREDIT_INVOICES_WITH_CUSTOMER_AND_SUBSCRIPTION = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/credit-invoices/'
        CREDIT_INVOICES_WITH_CUSTOMERS = \
            'api/finance/v1/customers/{cid}/credit-invoices/'
        EXPORT_CREDIT_INVOICES_WITH_CUSTOMER_AND_SUBSCRIPTION = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/credit-invoices/'
        CREDIT_INVOICES_WITH_SUBSCRIPTION = 'api/finance/v1/subscriptions/{' \
                                            'sid}/credit-invoices/'
        EXPORT_CREDIT_INVOICES_WITH_SUBSCRIPTION = 'api/finance/v1/export/{' \
                                                   'ex_type}/subscriptions/{' \
                                                   'sid}/credit-invoices/'
        EXPORT_CREDIT_INVOICES_WITH_CUSTOMER = 'api/finance/v1/export/{' \
                                               'ex_type}/customers/{' \
                                               'cid}/credit-invoices/'
        CREDIT_INVOICES = 'api/finance/v1/credit-invoices/'
        EXPORT_CREDIT_INVOICES = 'api/finance/v1/export/{' \
                                 'ex_type}/credit-invoices/'
        CREDIT_INVOICE = 'api/finance/v1/credit-invoices/{crid}/'
        CREDIT_INVOICE_WITH_SUBSCRIPTION = 'api/finance/v1/subscriptions/{' \
                                           'sid}/credit-invoices/{crid}/'
        CREDIT_INVOICE_WITH_CUSTOMER_AND_SUBSCRIPTION = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/credit-invoices/{crid}/'
        CREDIT_INVOICE_WITH_CUSTOMER = \
            'api/finance/v1/customers/{cid}/credit-invoices/{crid}/'
        PACKAGE_INVOICE_WITH_SUBSCRIPTIONS = 'api/finance/v1/subscriptions/{' \
                                             'sid}/package-invoices/{pid}/'
        PACKAGE_INVOICE_WITH_CUSTOMERS = 'api/finance/v1/customers/{' \
                                         'cid}/package-invoices/{pid}/'
        PACKAGE_INVOICE = 'api/finance/v1/package-invoices/{pid}/'
        PACKAGE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/package-invoices/'
        EXPORT_PACKAGE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/package-invoices/'
        EXPORT_PACKAGE_INVOICES_WITH_CUSTOMERS = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/package-invoices/'
        PACKAGE_INVOICES_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/subscriptions/{sid}/package-invoices/'
        PACKAGE_INVOICES_WITH_CUSTOMERS = \
            'api/finance/v1/customers/{cid}/package-invoices/'
        EXPORT_PACKAGE_INVOICES_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/export/{ex_type}/subscriptions/{' \
            'sid}/package-invoices/'
        PACKAGE_INVOICES = 'api/finance/v1/package-invoices/'
        EXPORT_PACKAGE_INVOICES = 'api/finance/v1/export/{' \
                                  'ex_type}/package-invoices/'
        PACKAGE_INVOICES_WITH_CUSTOMER = 'api/finance/v1/customers/{' \
                                         'cid}/package-invoices/'
        EXPORT_PACKAGE_INVOICES_WITH_CUSTOMER = 'api/finance/v1/export/{' \
                                                'ex_type}/customers/{' \
                                                'cid}/package-invoices/'

    class APILabels:
        CREATE_BASE_BALANCE_INVOICE = "Create new base balance invoice"
        CREATE_CREDIT_INVOICE = "Create new credit invoice"
        UPLOAD_INVOICE = "Upload invoice"
        CREATE_INTERIM_INVOICE = "Create new interim invoice"
        CREATE_PACKAGE_INVOICE = "Create new package invoice"
        UPDATE_PACKAGE_INVOICE = "Update package invoice"
