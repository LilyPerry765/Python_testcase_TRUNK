import datetime
import logging

from rspsrv.apps.invoice.versions.v1_0.services.invoice import InvoiceService
from rspsrv.apps.membership.versions.v1.services.customer import (
    CustomerService,
)
from rspsrv.apps.mis.versions.v1_0.services.mis import MisService
from rspsrv.apps.ocs.versions.v1_0.services.ocs import OcsService
from rspsrv.apps.payment.versions.v1_0.config import config as PaymentConfig
from rspsrv.apps.subscription import config as SubscriptionConfig
from rspsrv.apps.subscription.models import (
    Subscription,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.cache import Cache
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class Conversion:
    @classmethod
    def convert_base_balance_invoice_status_code(cls, status_code):
        if status_code == SubscriptionConfig.Subscription.BaseBalancePayment \
                .STATE_CHOICES.pending:
            return 'ready'
        elif status_code == \
                SubscriptionConfig.Subscription.BaseBalancePayment \
                        .STATE_CHOICES.paid:
            return 'success'

        return 'revoke'

    @classmethod
    def convert_payment_status_code(cls, status_code):
        if status_code == PaymentConfig.Payment.STATE_CHOICES.before_submit \
                or status_code == \
                PaymentConfig.Payment.STATE_CHOICES.after_submit:
            return 'pending'
        elif status_code == PaymentConfig.Payment.STATE_CHOICES.success:
            return 'success'
        return 'failed'


class ImportSubscription:
    @classmethod
    def import_subscriptions(cls, subscriptions):
        cgg_subscriptions = []
        failed_subscriptions = []

        for subscription in subscriptions:
            subscription['subscription_code'] = subscription.pop('product_id')
            try:
                customer = MisService.get_customer_code(
                    subscription['subscription_code'],
                )
            except api_exceptions.APIException as e:
                logger.error(
                    "Get customer code returned status {}, of {}".format(
                        e.status_code,
                        e.detail,
                    )
                )
                continue
            customer_id = None
            customer_obj = None
            if customer['CustomerId'] != '':
                customer_obj = CustomerService.create_customer(
                    customer['CustomerId'],
                )
                customer_id = customer_obj['id']

            customer_admin = CustomerService.create_or_get_default_user(
                customer['CustomerId']
            )
            subscription['customer_id'] = customer_id
            subscription['number'] = Helper.normalize_number(
                subscription.pop('main_number'),
            )
            subscription['destination_number'] = Helper.normalize_number(
                subscription['destination_number'],
            )
            subscription['destination_number_off'] = Helper.normalize_number(
                subscription['destination_number_off'],
            )
            cgg_subscriptions.append(
                {
                    'number': subscription['number'],
                    'subscription_code': subscription['subscription_code'],
                    'customer_id': subscription['customer_id'],
                    'base_balance': subscription['base_balance'],
                    'used_balance': subscription['used_balance'],
                    'activation': subscription['activation'],
                    'credit': subscription['gateway_credit'],
                    'base_balance_payment':
                        subscription['base_balance_payment']
                }
            )

            del subscription['id']
            del subscription['base_balance']
            del subscription['used_balance']
            del subscription['gateway_credit']
            del subscription['client_id']
            del subscription['last_audited_cdr']
            del subscription['conditional_list_id']
            del subscription['business_week_id']
            del subscription['base_balance_payment']
            ImportSubscription.save_subscriptions(subscription)
            if customer_admin['password'] and customer_obj:
                Cache.set(
                    'prime_migration',
                    {
                        'prime_code': customer_obj['prime_code'],
                    },
                    {
                        'id': customer_obj['id'],
                        'prime_code': customer_obj['prime_code'],
                        'username': customer_admin['username'],
                        'password': customer_admin['password'],
                    }
                )

        for cgg_subscription in cgg_subscriptions:
            try:
                OcsService.create_subscription(
                    customer_code=cgg_subscription['customer_id'],
                    subscription_code=cgg_subscription['subscription_code'],
                    number=cgg_subscription['number'],
                    base_balance=cgg_subscription['base_balance'],
                    used_balance=cgg_subscription['used_balance'],
                    is_active=cgg_subscription['activation'],
                    credit=cgg_subscription['credit'],
                    is_prepaid=False,
                )
            except Exception as e:
                if hasattr(e, 'status_code') and e.status_code == 409:
                    pass
                else:
                    failed_subscriptions.append(
                        cgg_subscription['subscription_code']
                    )
                    logger.warning(
                        "{}: {}".format(
                            cgg_subscription['subscription_code'],
                            str(e)
                        )
                    )

            base_balance_dicts_list = []
            for base_balance in cgg_subscription['base_balance_payment']:
                base_balance_dict = {}
                payments_list = []
                base_balance_dict['subscription_code'] = \
                    Subscription.objects.get(
                        number=cgg_subscription['number']
                    ).subscription_code
                base_balance_dict['status_code'] = \
                    Conversion.convert_base_balance_invoice_status_code(
                        base_balance['state']
                    )
                base_balance_dict['created_at'] = \
                    datetime.datetime.utcfromtimestamp(
                        base_balance['created_at']).strftime(
                        "%Y-%m-%d %H:%M:%S.%f",
                    )
                base_balance_dict['updated_at'] = \
                    datetime.datetime.utcfromtimestamp(
                        base_balance['updated_at']).strftime(
                        "%Y-%m-%d %H:%M:%S.%f",
                    )
                for payment in base_balance['payments']:
                    base_balance_dict['total_cost'] = payment['amount']
                    payments_list.append({
                        'amount': payment['amount'],
                        'updated_at': datetime.datetime.utcfromtimestamp(
                            payment['updated_at']).strftime(
                            "%Y-%m-%d %H:%M:%S.%f",
                        ),
                        'created_at': datetime.datetime.utcfromtimestamp(
                            payment['created_at']).strftime(
                            "%Y-%m-%d %H:%M:%S.%f",
                        ),
                        'gateway': payment['transaction_gateway'],
                        'extra_data': payment['mis_extra_data'],
                        'status_code':
                            Conversion.convert_payment_status_code(
                                payment['state']
                            ),
                    })
                if 'total_cost' not in base_balance_dict:
                    base_balance_dict['total_cost'] = 0
                base_balance_dict['payments'] = payments_list
                base_balance_dicts_list.append(
                    base_balance_dict,
                )

            try:
                InvoiceService.migrate_base_balance_invoices(
                    base_balance_dicts_list,
                )
            except api_exceptions.APIException:
                logger.info(
                    "Migrate base balance invoices failed"
                )

        logger.info({
            "Failed subscriptions": failed_subscriptions
        })

        return "Migrating subscription data Finished Successfully"

    @staticmethod
    def save_subscriptions(subscription):
        subscription_obj = None
        try:
            subscription_obj = Subscription(**subscription)
            subscription_obj.save()
        except Exception as e:
            print(e)
        if subscription_obj:
            Subscription.objects.filter(id=subscription_obj.id).update(
                updated_at=subscription['updated_at'],
                created_at=subscription['created_at']
            )
