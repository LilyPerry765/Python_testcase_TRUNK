import datetime
import logging
from math import ceil

from rspsrv.apps.invoice.models import BillTypeChoices
from rspsrv.apps.invoice.versions.v1_0.config import (
    BillConfig as InvoiceConfig,
)
from rspsrv.apps.invoice.versions.v1_0.services.invoice import InvoiceService
from rspsrv.apps.payment.apps import PaymentConfig
from rspsrv.apps.payment.versions.v1_0.config import config as PaymentConfig
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class Conversion:
    @classmethod
    def convert_to_nanoseconds(cls, duration):
        return duration * 1000000000

    @classmethod
    def convert_payment_status_code(cls, status_code):
        if status_code == PaymentConfig.Payment.STATE_CHOICES.before_submit \
                or status_code == \
                PaymentConfig.Payment.STATE_CHOICES.after_submit:
            return 'pending'
        elif status_code == PaymentConfig.Payment.STATE_CHOICES.success:
            return 'success'
        return 'failed'

    @classmethod
    def convert_invoice_type(cls, invoice_type):
        if invoice_type == BillTypeChoices[0][0]:
            return 'interim'
        return 'periodic'

    @classmethod
    def convert_invoice_status_code(cls, status_code):
        if status_code == InvoiceConfig.STATE_CHOICES.ready_to_pay:
            return 'ready'
        elif status_code == InvoiceConfig.STATE_CHOICES.pending:
            return 'pending'
        elif status_code == InvoiceConfig.STATE_CHOICES.paid:
            return 'success'
        return 'revoke'


class ImportInvoice:
    @classmethod
    def import_invoices(cls, invoices):
        invoice_dicts_list = []

        for invoice in invoices:
            payments_list = []
            invoice_dict = {
                'subscription_code': invoice['subscription_code'],
                'subscription_fee': invoice['subscription_cost'],
                'tax_percent': invoice['tax'],
                'tax_cost': ceil(float(invoice['tax_cost'])),
                'debt': invoice['debt'],
                'discount': invoice['credit'],
                'mobile_cost': invoice['total_outbound_cellphone_cost'],
                'mobile_usage': Conversion.convert_to_nanoseconds(
                    invoice['total_outbound_cellphone_duration'],
                ),
                'landlines_long_distance_usage':
                    Conversion.convert_to_nanoseconds(
                        invoice['total_outbound_landlines_duration'],
                    ),
                'landlines_long_distance_cost':
                    invoice['total_outbound_landlines_cost'],
                'description': invoice['description'],
                'status_code': Conversion.convert_invoice_status_code(
                    invoice['state'],
                ),
                'invoice_type': Conversion.convert_invoice_type(
                    invoice['bill_type']
                ),
                'from_date': datetime.datetime.utcfromtimestamp(
                    invoice['from_date']
                ).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'to_date': datetime.datetime.utcfromtimestamp(
                    invoice['to_date']).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'created_at': datetime.datetime.utcfromtimestamp(
                    invoice['created_at']
                ).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'updated_at': datetime.datetime.utcfromtimestamp(
                    invoice['updated_at']
                ).strftime("%Y-%m-%d %H:%M:%S.%f"),
            }

            for payment in invoice['payments']:
                payments_list.append(
                    {
                        'amount': payment['amount'],
                        'updated_at': datetime.datetime.utcfromtimestamp(
                            payment['updated_at']
                        ).strftime("%Y-%m-%d %H:%M:%S.%f"),
                        'created_at': datetime.datetime.utcfromtimestamp(
                            payment['created_at']
                        ).strftime("%Y-%m-%d %H:%M:%S.%f"),
                        'gateway': payment['transaction_gateway'],
                        'extra_data': payment['mis_extra_data'],
                        'status_code': Conversion.convert_payment_status_code(
                            payment['status_code'],
                        ),
                    }
                )
            invoice_dict['payments'] = payments_list
            invoice_dicts_list.append(
                invoice_dict,
            )
            if len(invoice_dicts_list) == 100:
                # Migrate 100 at a time
                try:
                    InvoiceService.migrate_invoices(
                        invoice_dicts_list,
                    )
                    invoice_dicts_list = []
                except api_exceptions.APIException as e:
                    return (
                        "Migrate invoices failed"
                    )
        if invoice_dicts_list:
            try:
                InvoiceService.migrate_invoices(
                    invoice_dicts_list,
                )
            except api_exceptions.APIException as e:
                return (
                    "Migrate invoices failed"
                )

        return (
            "Migrating invoices is completed"
        )
