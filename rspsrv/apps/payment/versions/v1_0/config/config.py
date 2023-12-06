from django.conf import settings
from django.utils.translation import gettext_lazy as _
from model_utils import Choices


class PaymentConfiguration:
    class Gateway:
        CREDIT = 'credit'
        OFFLINE = 'offline'

    class URLs:
        INVOICE_PAYMENTS = 'api/finance/v1/invoices/{iid}/payments/'
        EXPORT_INVOICE_PAYMENTS = 'api/finance/v1/export/{' \
                                  'ex_type}/invoices/{iid}/payments/'
        INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/subscriptions/{sid}/invoices/{iid}/payments/'
        INVOICE_PAYMENTS_WITH_CUSTOMERS = \
            'api/finance/v1/customers/{cid}/invoices/{iid}/payments/'
        EXPORT_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/export/{ex_type}/subscriptions/{sid}/invoices/{' \
            'iid}/payments/'
        EXPORT_INVOICE_PAYMENTS_WITH_CUSTOMERS = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/invoices/{' \
            'iid}/payments/'
        INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{sid}/invoices/{' \
            'iid}/payments/'
        EXPORT_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/invoices/{iid}/payments/'
        PAYMENTS = 'api/finance/v1/payments/'
        EXPORT_PAYMENTS = 'api/finance/v1/export/{ex_type}/payments/'
        PAYMENTS_BY_SUBSCRIPTION = 'api/finance/v1/subscriptions/{' \
                                   'sid}/payments/'
        PAYMENTS_BY_CUSTOMER = 'api/finance/v1/customers/{cid}/payments/'
        EXPORT_PAYMENTS_BY_SUBSCRIPTION = 'api/finance/v1/export/{' \
                                          'ex_type}/subscriptions/{' \
                                          'sid}/payments/'
        PAYMENTS_BY_CUSTOMER_AND_SUBSCRIPTION = 'api/finance/v1/customers/{' \
                                                'cid}/subscriptions/{' \
                                                'sid}/payments/'
        EXPORT_PAYMENTS_BY_CUSTOMER_AND_SUBSCRIPTION = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/payments/'
        PAYMENTS_BY_SUBSCRIPTION_AND_INVOICE = \
            'api/finance/v1/subscriptions/{sid}/invoices/{iid}/payments/'
        EXPORT_PAYMENTS_BY_SUBSCRIPTION_AND_INVOICE = \
            'api/finance/v1/export/{ex_type}/subscriptions/{sid}/invoices/{' \
            'iid}/payments/'
        EXPORT_PAYMENTS_BY_CUSTOMER = 'api/finance/v1/export/{' \
                                      'ex_type}/customers/{cid}/payments/'
        PAYMENTS_BY_INVOICE_ID = 'api/finance/v1/invoices/{iid}/payments/'
        EXPORT_PAYMENTS_BY_INVOICE_ID = 'api/finance/v1/export/{' \
                                        'ex_type}/invoices/{iid}/payments/'
        PAYMENTS_BY_BASE_BALANCE_INVOICE_ID = \
            'api/finance/v1/base-balance-invoices/{iid}/payments/'
        EXPORT_PAYMENTS_BY_BASE_BALANCE_INVOICE_ID = \
            'api/finance/v1/export/{ex_type}/base-balance-invoices/{' \
            'iid}/payments/'
        PAYMENT = 'api/finance/v1/payments/{pid}/'
        PAYMENT_APPROVAL = 'api/finance/v1/payments/{pid}/approval/'
        PAYMENT_WITH_CUSTOMER_AND_SUBSCRIPTIONS = \
            'api/finance/v1/customers/{cid}/subscriptions/{sid}/payments/{' \
            'pid}/'
        PAYMENT_WITH_SUBSCRIPTIONS = 'api/finance/v1/subscriptions/{' \
                                     'sid}/payments/{pid}/'
        BASE_BALANCE_INVOICE_PAYMENTS = \
            'api/finance/v1/base-balance-invoices/{iid}/payments/'
        EXPORT_BASE_BALANCE_INVOICE_PAYMENTS = 'api/finance/v1/export/{' \
                                               'ex_type}/base-balance-invoices/{iid}/payments/'
        BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/subscriptions/{sid}/base-balance-invoices/{' \
            'iid}/payments/'
        BASE_BALANCE_INVOICE_PAYMENTS_WITH_CUSTOMERS = \
            'api/finance/v1/customers/{cid}/base-balance-invoices/{' \
            'iid}/payments/'
        EXPORT_BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/export/{ex_type}/subscriptions/{' \
            'sid}/base-balance-invoices/{iid}/payments/'
        EXPORT_BASE_BALANCE_INVOICE_PAYMENTS_WITH_CUSTOMERS = \
            'api/finance/v1/export/{ex_type}/customers/{' \
            'cid}/base-balance-invoices/{iid}/payments/'
        BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/base-balance-invoices/{iid}/payments/'
        EXPORT_BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER \
            = 'api/finance/v1/export/{ex_type}/customers/{' \
              'cid}/subscriptions/{sid}/base-balance-invoices/{iid}/payments/'
        CREDIT_INVOICE_PAYMENTS = 'api/finance/v1/credit-invoices/{' \
                                  'crid}/payments/'
        EXPORT_CREDIT_INVOICE_PAYMENTS = 'api/finance/v1/export/{' \
                                         'ex_type}/credit-invoices/{' \
                                         'crid}/payments/'
        EXPORT_CREDIT_INVOICE_PAYMENTS_WITH_SUBSCRIPTION = \
            'api/finance/v1/export/{ex_type}/subscriptions/{' \
            'sid}/credit-invoices/{crid}/payments/'
        EXPORT_CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER = \
            'api/finance/v1/export/{ex_type}/customers/{' \
            'cid}/credit-invoices/{crid}/payments/'
        CREDIT_INVOICE_PAYMENTS_WITH_SUBSCRIPTION = \
            'api/finance/v1/subscriptions/{sid}/credit-invoices/{' \
            'crid}/payments/'
        CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER = \
            'api/finance/v1/customers/{cid}/credit-invoices/{' \
            'crid}/payments/'
        CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER_AND_SUBSCRIPTION = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/credit-invoices/{crid}/payments/'
        EXPORT_CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER_AND_SUBSCRIPTION = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/credit-invoices/{crid}/payments/'
        PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/customers/{cid}/subscriptions/{' \
            'sid}/package-invoices/{pid}/payments/'
        EXPORT_PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER = \
            'api/finance/v1/export/{ex_type}/customers/{cid}/subscriptions/{' \
            'sid}/package-invoices/{pid}/payments/'
        PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/subscriptions/{sid}/package-invoices/{' \
            'pid}/payments/'
        PACKAGE_INVOICE_PAYMENTS_WITH_CUSTOMERS = \
            'api/finance/v1/customers/{id}/package-invoices/{' \
            'pid}/payments/'
        EXPORT_PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS = \
            'api/finance/v1/export/{ex_type}/subscriptions/{' \
            'sid}/package-invoices/{pid}/payments/'
        EXPORT_PACKAGE_INVOICE_PAYMENTS_WITH_CUSTOMERS = \
            'api/finance/v1/export/{ex_type}/customers/{' \
            'cid}/package-invoices/{pid}/payments/'
        PACKAGE_INVOICE = 'api/finance/v1/package-invoices/{pid}/'
        PACKAGE_INVOICE_PAYMENTS = 'api/finance/v1/package-invoices/{' \
                                   'pid}/payments/'
        EXPORT_PACKAGE_INVOICE_PAYMENTS = 'api/finance/v1/export/{' \
                                          'ex_type}/package-invoices/{' \
                                          'pid}/payments/'

    class APILabels:
        CREATE_PAYMENT = "Create new payment"
        APPROVE_PAYMENT = "Approve payment"


# Deprecate this
class Payment:
    STATE_CHOICES = Choices(
        (0, 'before_submit', _('Before Submit')),
        (1, 'after_submit', _('After Submit')),
        (2, 'success', _('Success')),
        (3, 'failed', _('Failed')),
    )

    @staticmethod
    def gateways_choices(return_list=False):
        """
        List of Payment Gateways as Choices Format.
        e.g: [('payir', 'payir'), ('offline', 'offline')]

        :return:
        """
        gateways = []

        for gateway in settings.PAYMENT_GATEWAYS:
            if return_list:
                gateways.append(gateway)
            else:
                gateways.append((gateway, gateway))

        return gateways

    def __init__(self):
        pass


# Deprecate this
class Transaction:
    STATE_CHOICES = Choices(
        (0, 'pending', _('Pending')),
        (1, 'success', _('Success')),
        (2, 'failed', _('Failed')),
    )

    def __init__(self):
        pass
