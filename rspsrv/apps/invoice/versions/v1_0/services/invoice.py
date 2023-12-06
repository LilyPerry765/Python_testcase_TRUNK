# --------------------------------------------------------------------------
# This service should not be responsible for ACL related tasks
# As a rule of thumb know that customer_code in CGG is Customer.id here
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - invoice.py
# Created at 2020-5-29,  11:53:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import logging

from django.utils.translation import gettext as _

from rspsrv.apps.cgg.versions.v1_0.services.cgg_service import CggService
from rspsrv.apps.invoice.versions.v1_0.config import InvoiceConfiguration
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")

CGG_URLS = InvoiceConfiguration.URLs


class InvoiceService:

    @classmethod
    def export_invoices(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if query_params is None:
            query_params = []

        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_INVOICES
            relative_uri = relative_uri.format(
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.EXPORT_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_INVOICES_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                ex_type=export_type,
            )
        else:
            relative_uri = \
                CGG_URLS.EXPORT_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                ex_type=export_type,
            )

        url = CggService.cgg_url(relative_uri, query_params)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_invoices(
            cls,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if query_params is None:
            query_params = []

        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.INVOICES
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(sid=subscription_code)
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.INVOICES_WITH_CUSTOMER
            relative_uri = relative_uri.format(cid=customer_code)
        else:
            relative_uri = CGG_URLS.INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
            )

        url = CggService.cgg_url(
            relative_uri,
            query_params,
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE if
            'bypass_pagination' in query_params else
            CggService.ResponseType.LIST,
        )

        return response

    @classmethod
    def get_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            invoice_id=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_url = CGG_URLS.INVOICE
            relative_url = relative_url.format(
                iid=invoice_id
            )
        elif customer_code is None and subscription_code is not None:
            relative_url = CGG_URLS.INVOICE_WITH_SUBSCRIPTIONS
            relative_url = relative_url.format(
                sid=subscription_code,
                iid=invoice_id
            )
        elif customer_code is not None and subscription_code is None:
            relative_url = CGG_URLS.INVOICE_WITH_CUSTOMERS
            relative_url = relative_url.format(
                cid=customer_code,
                iid=invoice_id
            )
        else:
            relative_url = CGG_URLS.INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code,
                iid=invoice_id
            )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )
        return response

    @classmethod
    def create_interim_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            on_demand=False,
    ):
        if customer_code is None and subscription_code is None:
            raise api_exceptions.ValidationError400(
                _("Subscription code can not be emtpy"),
            )
        elif customer_code is None and subscription_code:
            relative_url = CGG_URLS.INTERIM_INVOICE
            relative_url = relative_url.format(sid=subscription_code)
        else:
            relative_url = CGG_URLS.INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code,
            )

        query_params = {}
        if on_demand:
            query_params['on_demand'] = 1
        url = CggService.cgg_url(relative_url, query_params)
        response = CggService.cgg_response(
            url,
            http_method='post',
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_base_balance_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            base_balance_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICE
            relative_uri = relative_uri.format(
                iid=base_balance_id
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICE_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                iid=base_balance_id
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICE_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                iid=base_balance_id
            )
        else:
            relative_uri = \
                CGG_URLS.BASE_BALANCE_INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                iid=base_balance_id
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def export_base_balance_invoices(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_BASE_BALANCE_INVOICES
            relative_uri = relative_uri.format(
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = \
                CGG_URLS.EXPORT_BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = \
                CGG_URLS.EXPORT_BASE_BALANCE_INVOICES_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                ex_type=export_type,
            )
        else:
            relative_uri = \
                CGG_URLS.EXPORT_BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                ex_type=export_type,
            )

        url = CggService.cgg_url(
            relative_uri,
            query_params
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_base_balance_invoices(
            cls,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICES
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.BASE_BALANCE_INVOICES_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
            )
        else:
            relative_uri = \
                CGG_URLS.BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code
            )

        url = CggService.cgg_url(
            relative_uri,
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
    def create_new_base_balance_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            payload=None
    ):
        relative_uri = None
        if subscription_code is None:
            raise api_exceptions.ValidationError400({
                'subscription_code': _('required fields')
            })
        if customer_code is None and subscription_code is not None:
            relative_uri = \
                CGG_URLS.BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is not None:
            relative_uri = CGG_URLS \
                .BASE_BALANCE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                sid=subscription_code,
                cid=customer_code
            )

        url = CggService.cgg_url(relative_uri)

        if not isinstance(payload, dict) and not isinstance(payload, list):
            try:
                payload = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError:
                raise api_exceptions.ValidationError400(
                    _('JSON is Not Valid')
                )

        if 'to_credit' in payload:
            payload.pop('to_credit')

        response = CggService.cgg_response(
            url,
            body=payload,
            http_method='post',
            response_type=CggService.ResponseType.SINGLE,
        )
        return response

    @classmethod
    def migrate_base_balance_invoices(cls, base_balance_dicts):
        relative_url = CGG_URLS.MIGRATE_BASE_BALANCES
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            body=base_balance_dicts,
            http_method='post'
        )

        return response

    @classmethod
    def migrate_invoices(cls, invoice_dicts):
        relative_url = CGG_URLS.MIGRATE_INVOICES
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            body=invoice_dicts,
            http_method='post'
        )

        return response

    @classmethod
    def get_credit_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            credit_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICE
            relative_uri = relative_uri.format(
                crid=credit_id
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.CREDIT_INVOICE_WITH_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code,
                crid=credit_id
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICE_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                crid=credit_id
            )
        else:
            relative_uri = \
                CGG_URLS.CREDIT_INVOICE_WITH_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                crid=credit_id
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_credit_invoices(
            cls,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICES
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.CREDIT_INVOICES_WITH_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICES_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
            )
        else:
            relative_uri = \
                CGG_URLS.CREDIT_INVOICES_WITH_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code
            )
        # Make it friendly
        query_params = query_params.dict()
        query_params.update(
            {
                "friendly": 1
            }
        )
        url = CggService.cgg_url(
            relative_uri,
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
    def export_credit_invoices(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_CREDIT_INVOICES
            relative_uri = relative_uri.format(
                ex_type=export_type
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.EXPORT_CREDIT_INVOICES_WITH_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_CREDIT_INVOICES_WITH_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                ex_type=export_type,
            )
        else:
            relative_uri = CGG_URLS \
                .EXPORT_CREDIT_INVOICES_WITH_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                ex_type=export_type,
            )

        # Make it friendly
        query_params = query_params.dict()
        query_params.update(
            {
                "friendly": 1
            }
        )
        url = CggService.cgg_url(
            relative_uri,
            query_params
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def create_credit_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            payload=None,
    ):
        relative_uri = None
        if subscription_code is None and customer_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICES
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.CREDIT_INVOICES_WITH_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is not None:
            relative_uri = \
                CGG_URLS.CREDIT_INVOICES_WITH_CUSTOMER_AND_SUBSCRIPTION
            relative_uri = relative_uri.format(
                sid=subscription_code,
                cid=customer_code
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.CREDIT_INVOICES_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code
            )
        if not isinstance(payload, dict) and not isinstance(payload, list):
            try:
                payload = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError:
                raise api_exceptions.ValidationError400(
                    _('JSON is Not Valid')
                )
        if "operation_type" not in payload:
            payload['operation_type'] = \
                InvoiceConfiguration.OperationTypes.INCREASE
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            body=payload,
            http_method='post',
            response_type=CggService.ResponseType.SINGLE,
        )

        if response['data']['operation_type'] == \
                InvoiceConfiguration.OperationTypes.DECREASE and not \
                SubscriptionService.get_outbound_calls_status(
                    response['data']['subscription_code']
                ):
            used_for = response['data']['used_for']
            if used_for == InvoiceConfiguration.InvoiceTypes.INVOICE:
                SubscriptionService.enable_activation(
                    subscription_code=response['data']['subscription_code'],
                )
                SubscriptionService.enable_outbound_calls(
                    subscription_code=response['data']['subscription_code'],
                    check_prepaid=True,
                )
            if used_for == InvoiceConfiguration.InvoiceTypes.PACKAGE_INVOICE:
                SubscriptionService.enable_outbound_calls(
                    subscription_code=response['data']['subscription_code'],
                )

        return response

    @classmethod
    def update_package_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            package_invoice_id=None,
            payload=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE
            relative_uri = relative_uri.format(
                pid=package_invoice_id,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                pid=package_invoice_id,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                pid=package_invoice_id,
            )
        else:
            relative_uri = \
                CGG_URLS.PACKAGE_INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                pid=package_invoice_id,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            http_method='patch',
            body=payload,
            response_type=CggService.ResponseType.SINGLE
        )

        return response

    @classmethod
    def get_package_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            package_invoice_id=None
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE
            relative_uri = relative_uri.format(
                pid=package_invoice_id,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                pid=package_invoice_id,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICE_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                pid=package_invoice_id,
            )
        else:
            relative_uri = \
                CGG_URLS.PACKAGE_INVOICE_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                pid=package_invoice_id,
            )

        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def export_package_invoices(
            cls,
            export_type,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_PACKAGE_INVOICES
            relative_uri = relative_uri.format(
                ex_type=export_type,
            )
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.EXPORT_PACKAGE_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code,
                ex_type=export_type,
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.EXPORT_PACKAGE_INVOICES_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
                ex_type=export_type,
            )
        else:
            relative_uri = CGG_URLS \
                .EXPORT_PACKAGE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code,
                ex_type=export_type,
            )

        url = CggService.cgg_url(
            relative_uri,
            query_params
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.EXPORT,
        )

        return response

    @classmethod
    def get_package_invoices(
            cls,
            customer_code=None,
            subscription_code=None,
            query_params=None,
    ):
        if customer_code is None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICES
        elif customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PACKAGE_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is None:
            relative_uri = CGG_URLS.PACKAGE_INVOICES_WITH_CUSTOMERS
            relative_uri = relative_uri.format(
                cid=customer_code,
            )
        else:
            relative_uri = \
                CGG_URLS.PACKAGE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
            relative_uri = relative_uri.format(
                cid=customer_code,
                sid=subscription_code
            )

        url = CggService.cgg_url(
            relative_uri,
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
    def create_new_package_invoice(
            cls,
            customer_code=None,
            subscription_code=None,
            payload=None
    ):
        relative_uri = None
        if subscription_code is None:
            raise api_exceptions.ValidationError400({
                'subscription_code': _('required fields')
            })
        if customer_code is None and subscription_code is not None:
            relative_uri = CGG_URLS.PACKAGE_INVOICES_WITH_SUBSCRIPTIONS
            relative_uri = relative_uri.format(
                sid=subscription_code
            )
        elif customer_code is not None and subscription_code is not None:
            relative_uri = CGG_URLS \
                .PACKAGE_INVOICES_WITH_SUBSCRIPTIONS_AND_CUSTOMER
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
