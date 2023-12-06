# --------------------------------------------------------------------------
# As a rule of thumb know that customer_code in CGG is Customer.id here
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - payment.py
# Created at 2020-8-10,  11:18:34
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import logging

from django.utils.translation import gettext as _

from rspsrv.apps.cgg.versions.v1_0.services.cgg_service import CggService
from rspsrv.apps.invoice.versions.v1_0.config import InvoiceConfiguration
from rspsrv.apps.payment.versions.v1_0.config.config import (
    PaymentConfiguration,
)
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService
)
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")
CGG_URLS = PaymentConfiguration.URLs


class PaymentService:

    @classmethod
    def get_payments(
            cls,
            customer_code=None,
            subscription_code=None,
            invoice_id=None,
            base_balance_invoice_id=None,
            query_params=None,
    ):
        relative_url = None
        if subscription_code is None and customer_code is None and \
                invoice_id is None:
            relative_url = CGG_URLS.PAYMENTS
        elif subscription_code is not None and customer_code is None and \
                invoice_id is None:
            relative_url = CGG_URLS.PAYMENTS_BY_SUBSCRIPTION
            relative_url = relative_url.format(
                sid=subscription_code
            )
        elif subscription_code is not None and customer_code is not None and \
                invoice_id is None:
            relative_url = CGG_URLS.PAYMENTS_BY_CUSTOMER_AND_SUBSCRIPTION
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code
            )
        elif subscription_code is not None and customer_code is None and \
                base_balance_invoice_id is not None:
            relative_url = CGG_URLS.PAYMENTS_BY_SUBSCRIPTION_AND_INVOICE
            relative_url = relative_url.format(
                iid=base_balance_invoice_id,
                sid=subscription_code
            )
        elif subscription_code is None and customer_code is not None and \
                invoice_id is None:
            relative_url = CGG_URLS.PAYMENTS_BY_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code
            )
        elif subscription_code is None and customer_code is None and \
                invoice_id is not None:
            # by invoice id
            relative_url = CGG_URLS.PAYMENTS_BY_INVOICE_ID
            relative_url = relative_url.format(
                iid=invoice_id
            )
        elif subscription_code is None and customer_code is None and \
                base_balance_invoice_id is not None:
            # by invoice id
            relative_url = CGG_URLS.PAYMENTS_BY_BASE_BALANCE_INVOICE_ID
            relative_url = relative_url.format(
                iid=base_balance_invoice_id
            )

        if relative_url is None:
            raise api_exceptions.ValidationError400({
                'non_fields': _('can not create url')
            })

        url = CggService.cgg_url(
            relative_url,
            query_params
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE if
            'bypass_pagination' in query_params else
            CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def export_payments(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            invoice_id=None,
            base_balance_invoice_id=None,
            query_params=None,
    ):
        relative_url = None
        if subscription_code is None and customer_code is None and \
                invoice_id is None:
            # all payments
            relative_url = CGG_URLS.EXPORT_PAYMENTS
            relative_url = relative_url.format(
                ex_type=export_type,
            )
        elif subscription_code is not None and customer_code is None and \
                invoice_id is None:
            relative_url = CGG_URLS.EXPORT_PAYMENTS_BY_SUBSCRIPTION
            relative_url = relative_url.format(
                sid=subscription_code,
                ex_type=export_type,
            )
        elif subscription_code is not None and customer_code is not None and \
                invoice_id is None:
            relative_url = \
                CGG_URLS.EXPORT_PAYMENTS_BY_CUSTOMER_AND_SUBSCRIPTION
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code,
                ex_type=export_type,
            )
        elif subscription_code is not None and customer_code is None and \
                invoice_id is not None:
            relative_url = \
                CGG_URLS.EXPORT_PAYMENTS_BY_SUBSCRIPTION_AND_INVOICE
            relative_url = relative_url.format(
                iid=invoice_id,
                sid=subscription_code,
                ex_type=export_type,
            )
        elif subscription_code is not None and customer_code is None and \
                base_balance_invoice_id is not None:
            relative_url = \
                CGG_URLS.EXPORT_PAYMENTS_BY_SUBSCRIPTION_AND_INVOICE
            relative_url = relative_url.format(
                iid=base_balance_invoice_id,
                sid=subscription_code,
                ex_type=export_type,
            )
        elif subscription_code is None and customer_code is not None and \
                invoice_id is None:
            relative_url = CGG_URLS.EXPORT_PAYMENTS_BY_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code,
                ex_type=export_type,
            )
        elif subscription_code is None and customer_code is None and \
                invoice_id is not None:
            # by invoice id
            relative_url = CGG_URLS.EXPORT_PAYMENTS_BY_INVOICE_ID
            relative_url = relative_url.format(
                iid=invoice_id,
                ex_type=export_type,
            )
        elif subscription_code is None and customer_code is None and \
                base_balance_invoice_id is not None:
            # by invoice id
            relative_url = CGG_URLS.EXPORT_PAYMENTS_BY_BASE_BALANCE_INVOICE_ID
            relative_url = relative_url.format(
                iid=base_balance_invoice_id,
                ex_type=export_type,
            )

        if relative_url is None:
            raise api_exceptions.ValidationError400({
                'non_fields': _('can not create url')
            })

        url = CggService.cgg_url(
            relative_url,
            query_params
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_payment(
            cls,
            customer_code=None,
            subscription_code=None,
            payment_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.PAYMENT
            relative_uri = relative_uri.format(
                pid=payment_id,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PAYMENT_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                pid=payment_id,
            )
        else:
            relative_uri = CGG_URLS.PAYMENTS_BY_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                cid=subscription_code,
                sid=subscription_code,
                pid=payment_id,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_base_balance_invoice_payments(
            cls,
            customer_code=None,
            subscription_code=None,
            base_balance_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICE_PAYMENTS
            relative_uri = relative_uri.format(
                iid=base_balance_id
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = \
                CGG_URLS.BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                iid=base_balance_id
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = \
                CGG_URLS.BASE_BALANCE_INVOICE_PAYMENTS_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                iid=base_balance_id
            )
        else:
            relative_uri = CGG_URLS \
                .BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                iid=base_balance_id
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def create_new_payment(
            cls,
            customer_code=None,
            subscription_code=None,
            payload=None,
    ):
        relative_uri = None
        if subscription_code is None and customer_code is None:
            relative_uri = CGG_URLS.PAYMENTS
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PAYMENTS_BY_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.PAYMENTS_BY_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code
            )
        elif customer_code is not None and subscription_code is not None:
            relative_uri = CGG_URLS.PAYMENTS_BY_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code,
                cid=customer_code
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            body=payload,
            http_method='post',
            response_type=CggService.ResponseType.SINGLE,
        )
        return response

    @classmethod
    def approval_payment(
            cls,
            payment_id,
            status_code=False,
    ):
        rel_url = CGG_URLS.PAYMENT_APPROVAL
        rel_url = rel_url.format(pid=payment_id)
        url = CggService.cgg_url(rel_url)
        body = {
            'status_code': 'failed',
        }
        if status_code:
            body = {
                'status_code': 'success',
            }

        return CggService.cgg_response(
            url,
            body=body,
            http_method='post',
            response_type=CggService.ResponseType.SINGLE,
        )

    @classmethod
    def update_payment(
            cls,
            payment_id,
            status_code=False,
            extra_data=None
    ):
        if extra_data is None:
            extra_data = {}
        relative_url = CGG_URLS.PAYMENT
        relative_url = relative_url.format(pid=payment_id)
        url = CggService.cgg_url(relative_url)
        body = {
            'status_code': 'failed',
            'extra_data': extra_data,
        }
        if status_code:
            body = {
                'status_code': 'success',
                'extra_data': extra_data,
            }
        try:
            cgg_res = CggService.cgg_response(
                url,
                body=body,
                http_method='patch',
                response_type=CggService.ResponseType.SINGLE,
            )
        except api_exceptions.APIException as e:
            raise api_exceptions.APIException(e)

        if cgg_res['data']['should_enable'] and not \
                SubscriptionService.get_outbound_calls_status(
                    cgg_res['data']['subscription_code']
                ):
            used_for = cgg_res['data']['used_for']
            if used_for == InvoiceConfiguration.InvoiceTypes.INVOICE:
                SubscriptionService.enable_outbound_calls(
                    subscription_code=cgg_res['data']['subscription_code'],
                    check_prepaid=True,
                )
                SubscriptionService.enable_activation(
                    subscription_code=cgg_res['data']['subscription_code'],
                )
            if used_for == InvoiceConfiguration.InvoiceTypes.PACKAGE_INVOICE:
                SubscriptionService.enable_outbound_calls(
                    subscription_code=cgg_res['data']['subscription_code'],
                )

        return cgg_res

    @classmethod
    def export_credit_invoice_payments(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            credit_id=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_CREDIT_INVOICE_PAYMENTS
            relative_uri = relative_uri.format(
                crid=credit_id,
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS \
                .EXPORT_CREDIT_INVOICE_PAYMENTS_WITH_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code,
                crid=credit_id,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS \
                .EXPORT_CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                crid=credit_id,
                ex_type=export_type,
            )
        else:
            relative_uri = \
                CGG_URLS.EXPORT_CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                crid=credit_id,
                ex_type=export_type,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_credit_invoice_payments(
            cls,
            customer_code=None,
            subscription_code=None,
            credit_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICE_PAYMENTS
            relative_uri = relative_uri.format(
                crid=credit_id
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.CREDIT_INVOICE_PAYMENTS_WITH_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code,
                crid=credit_id
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                crid=credit_id
            )
        else:
            relative_uri = CGG_URLS \
                .CREDIT_INVOICE_PAYMENTS_WITH_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                crid=credit_id
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def export_package_invoice_payments(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            package_invoice_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_PACKAGE_INVOICE_PAYMENTS
            relative_uri = relative_uri.format(
                pid=package_invoice_id,
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS \
                .EXPORT_PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                pid=package_invoice_id,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS \
                .EXPORT_PACKAGE_INVOICE_PAYMENTS_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                pid=package_invoice_id,
                ex_type=export_type,
            )
        else:
            relative_uri = CGG_URLS \
                .EXPORT_PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                pid=package_invoice_id,
                ex_type=export_type,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_package_invoice_payments(
            cls,
            customer_code=None,
            subscription_code=None,
            package_invoice_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_PAYMENTS
            relative_uri = relative_uri.format(
                pid=package_invoice_id,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                pid=package_invoice_id,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_PAYMENTS_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                pid=package_invoice_id,
            )
        else:
            relative_uri = CGG_URLS \
                .PACKAGE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                pid=package_invoice_id,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def get_invoice_payments(
            cls,
            customer_code=None,
            subscription_code=None,
            invoice_id=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_url = CGG_URLS.INVOICE_PAYMENTS
            relative_url = relative_url.format(
                iid=invoice_id
            )
        elif customer_code is not None and subscription_code is None:
            relative_url = CGG_URLS.INVOICE_PAYMENTS_WITH_CUSTOMERS
            relative_url = relative_url.format(
                cid=customer_code,
                iid=invoice_id
            )
        elif customer_code is None and subscription_code is not None:
            relative_url = CGG_URLS.INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS
            relative_url = relative_url.format(
                sid=subscription_code,
                iid=invoice_id
            )
        else:
            relative_url = \
                CGG_URLS.INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code,
                iid=invoice_id
            )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def export_invoice_payments(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            invoice_id=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_url = CGG_URLS.EXPORT_INVOICE_PAYMENTS
            relative_url = relative_url.format(
                iid=invoice_id,
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_url = CGG_URLS.EXPORT_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS
            relative_url = relative_url.format(
                sid=subscription_code,
                iid=invoice_id,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_url = CGG_URLS.EXPORT_INVOICE_PAYMENTS_WITH_CUSTOMERS
            relative_url = relative_url.format(
                cid=customer_code,
                iid=invoice_id,
                ex_type=export_type,
            )
        else:
            relative_url = \
                CGG_URLS.EXPORT_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code,
                iid=invoice_id,
                ex_type=export_type,
            )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def export_base_balance_invoice_payments(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            base_balance_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_BASE_BALANCE_INVOICE_PAYMENTS
            relative_uri = relative_uri.format(
                iid=base_balance_id,
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = \
                CGG_URLS.EXPORT_BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                iid=base_balance_id,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = \
                CGG_URLS.EXPORT_BASE_BALANCE_INVOICE_PAYMENTS_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                iid=base_balance_id,
                ex_type=export_type,
            )
        else:
            relative_uri = CGG_URLS \
                .EXPORT_BASE_BALANCE_INVOICE_PAYMENTS_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                iid=base_balance_id,
                ex_type=export_type,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response
