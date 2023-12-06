# --------------------------------------------------------------------------
# This service should not be responsible for ACL related tasks
# (C) 2020 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - ocs.py
# Created at 2020-6-15,  14:53:13
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
import logging
from datetime import datetime, timedelta

from django.utils.translation import gettext as _

from rspsrv.apps.cgg.versions.v1_0.services.cgg_service import CggService
from rspsrv.apps.cgg.versions.v1_0.tasks import send_notification_to_mis
from rspsrv.apps.mis.versions.v1_0.config import Notification
from rspsrv.apps.ocs.versions.v1_0.config import OcsConfiguration
from rspsrv.apps.ocs.versions.v1_0.serializers.notify import (
    NotifyInvoiceSerializer,
    NotifySubscriptionSerializer,
)
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class OcsService:

    @classmethod
    def postpaid_max_usage(cls, body):
        """
        Get notification from CGG on postpaid max usage
        :param body:
        :type body:
        """
        body = Helper.get_dict_from_json(body)
        max_usage = NotifySubscriptionSerializer(
            data=body,
        )
        if max_usage.is_valid(raise_exception=True):
            max_usage = max_usage.data
        if max_usage is not None:
            if SubscriptionService.disable_outbound_calls(
                    max_usage['subscription_code'],
            ):
                send_notification_to_mis.delay(
                    max_usage['customer_code'],
                    Notification.PostpaidMaxUsage().get_email_subject(),
                    Notification.PostpaidMaxUsage().get_email(
                        max_usage['number'],
                    ),
                    Notification.PostpaidMaxUsage().get_sms(
                        max_usage['number'],
                    ),
                )

    @classmethod
    def automatic_deallocation(
            cls,
            warning_type,
            body,
    ):
        """
        Get notification from CGG on deallocation
        :param warning_type: could be 1 or 2
        :type warning_type:

        :param body:
        :type body:
        """
        body = Helper.get_dict_from_json(body)
        objects = NotifySubscriptionSerializer(
            data=body,
            many=True,
        )
        if objects.is_valid(raise_exception=True):
            objects = objects.data
        deallocate_class = Notification.DeallocationWarning1
        if int(warning_type) == 2:
            deallocate_class = Notification.DeallocationWarning2
        if objects is not None:
            for obj in objects:
                if int(warning_type) == 2:
                    #SubscriptionService.deallocate_subscription(
                    #    obj['subscription_code'],
                    #)
                    cls.deallocate_subscription(
                        obj['subscription_code'],
                        body={}
                    )
                #send_notification_to_mis.delay(
                #    obj['customer_code'],
                #    deallocate_class().get_email_subject(),
                #    deallocate_class().get_email(
                #        obj['number'],
                #    ),
                #    deallocate_class().get_sms(
                #        obj['number'],
                #    ),
                #)

    @classmethod
    def due_date(cls, warning_type, body):
        """
        Get notification from CGG on invoice due date
        :param warning_type: could be 1,2,3,4
        :type warning_type:
        :param body:
        :type body:
        """
        invoices_object = None
        body = Helper.get_dict_from_json(body)
        invoice_serializer = NotifyInvoiceSerializer(
            data=body,
            many=True,
        )
        if invoice_serializer.is_valid(raise_exception=True):
            invoices_object = invoice_serializer.data
        due_date_class = Notification.DueDateWarning1
        if int(warning_type) == 2:
            due_date_class = Notification.DueDateWarning2
        elif int(warning_type) == 3:
            due_date_class = Notification.DueDateWarning3
        elif int(warning_type) == 4:
            due_date_class = Notification.DueDateWarning4
        if invoices_object is not None:
            for invoice_object in invoices_object:
                if int(warning_type) == 3:
                    SubscriptionService.disable_outbound_calls(
                        invoice_object['subscription_code'],
                    )
                if int(warning_type) == 4:
                    SubscriptionService.disable_activation(
                        invoice_object['subscription_code'])
                    SubscriptionService.disable_outbound_calls(
                        invoice_object['subscription_code'],
                    )
                send_notification_to_mis.delay(
                    invoice_object['customer_code'],
                    due_date_class().get_email_subject(),
                    due_date_class().get_email(
                        invoice_object['number'],
                        invoice_object['total_cost'],
                        invoice_object['cause'],
                    ),
                    due_date_class().get_sms(
                        invoice_object['number'],
                        invoice_object['total_cost'],
                        invoice_object['cause'],
                    ),
                )

    @classmethod
    def periodic_invoices(cls, body):
        """
        Get notification from CGG on periodic invoices
        :param body:
        :type body:
        """
        invoices_object = None
        body = Helper.get_dict_from_json(body)
        invoice_serializer = NotifyInvoiceSerializer(
            data=body,
            many=True,
        )
        if invoice_serializer.is_valid(raise_exception=True):
            invoices_object = invoice_serializer.data
        if invoices_object is not None:
            wait_in_minutes = Helper.time_difference_in_minutes(
                to_hour=8,
                to_minute=30,
                time_zone="Asia/Tehran"
            )
            apply_time = datetime.now() + timedelta(minutes=wait_in_minutes)
            for invoice_object in invoices_object:
                if invoice_object["auto_payed"]:
                    SubscriptionService.enable_outbound_calls(
                        invoice_object['subscription_code'],
                        check_prepaid=True,
                    )
                    SubscriptionService.enable_activation(
                        invoice_object['subscription_code'],
                    )
                    send_notification_to_mis.apply_async(
                        args=(
                            invoice_object['customer_code'],
                            Notification.AutoPayPeriodic().get_email_subject(),
                            Notification.AutoPayPeriodic().get_email(
                                invoice_object['number'],
                                invoice_object['total_cost'],
                            ),
                            Notification.AutoPayPeriodic().get_sms(
                                invoice_object['number'],
                                invoice_object['total_cost'],
                            ),
                        ),
                        eta=apply_time,
                    )
                else:
                    send_notification_to_mis.apply_async(
                        args=(
                            invoice_object['customer_code'],
                            Notification.PeriodicInvoice().get_email_subject(),
                            Notification.PeriodicInvoice().get_email(
                                invoice_object['number'],
                                invoice_object['total_cost'],
                            ),
                            Notification.PeriodicInvoice().get_sms(
                                invoice_object['number'],
                                invoice_object['total_cost'],
                            ),
                        ),
                        eta=apply_time,
                    )

    @classmethod
    def interim_invoice(cls, body):
        """
        Get notification from CGG on interim invoice
        :param body:
        :type body:
        """
        invoice_object = None
        body = Helper.get_dict_from_json(body)
        invoice_serializer = NotifyInvoiceSerializer(
            data=body,
        )
        if invoice_serializer.is_valid(raise_exception=True):
            invoice_object = invoice_serializer.data
        if invoice_object is not None:
            send_notification_to_mis.delay(
                invoice_object['customer_code'],
                Notification.InterimInvoice().get_email_subject(),
                Notification.InterimInvoice().get_email(
                    invoice_object['number'],
                    invoice_object['total_cost'],
                    invoice_object['cause'],
                ),
                Notification.InterimInvoice().get_sms(
                    invoice_object['number'],
                    invoice_object['total_cost'],
                    invoice_object['cause'],
                ),
            )

    @classmethod
    def interim_invoice_auto_payed(cls, body):
        """
        Get notification from CGG on auto payed interim invoice
        :param body:
        :type body:
        """
        invoice_object = None
        body = Helper.get_dict_from_json(body)
        invoice_serializer = NotifyInvoiceSerializer(
            data=body,
        )
        if invoice_serializer.is_valid(raise_exception=True):
            invoice_object = invoice_serializer.data
        if invoice_object is not None:
            if SubscriptionService.enable_outbound_calls(
                    invoice_object['subscription_code'],
            ) and SubscriptionService.enable_activation(
                invoice_object['subscription_code'],
            ):
                send_notification_to_mis.delay(
                    invoice_object['customer_code'],
                    Notification.AutoPayInterim().get_email_subject(),
                    Notification.AutoPayInterim().get_email(
                        invoice_object['number'],
                        invoice_object['total_cost'],
                        invoice_object['cause'],
                    ),
                    Notification.AutoPayInterim().get_sms(
                        invoice_object['number'],
                        invoice_object['total_cost'],
                        invoice_object['cause'],
                    ),
                )

    @classmethod
    def prepaid_expired(cls, body):
        """
        Get notification from CGG on prepaid expiry
        :param body:
        :type body:
        """
        prepaid_object = None
        body = Helper.get_dict_from_json(body)
        prepaid_serializer = NotifySubscriptionSerializer(
            data=body,
        )
        if prepaid_serializer.is_valid(raise_exception=True):
            prepaid_object = prepaid_serializer.data
        SubscriptionService.disable_outbound_calls(
            prepaid_object['subscription_code'],
            check_prepaid=True,
        )
        if prepaid_object is not None:
            send_notification_to_mis.delay(
                prepaid_object['customer_code'],
                Notification.PrepaidExpired().get_email_subject(),
                Notification.PrepaidExpired().get_email(
                    prepaid_object['number'],
                ),
                Notification.PrepaidExpired().get_sms(
                    prepaid_object['number'],
                ),
            )

    @classmethod
    def prepaid_renewed(cls, body):
        """
        Get notification from CGG on renewal of prepaid
        :param body:
        :type body:
        """
        prepaid_object = None
        body = Helper.get_dict_from_json(body)
        prepaid_serializer = NotifySubscriptionSerializer(
            data=body,
        )
        if prepaid_serializer.is_valid(raise_exception=True):
            prepaid_object = prepaid_serializer.data
        if prepaid_object is not None:
            SubscriptionService.enable_outbound_calls(
                prepaid_object['subscription_code'],
            )
            send_notification_to_mis.delay(
                prepaid_object['customer_code'],
                Notification.PrepaidRenewed().get_email_subject(),
                Notification.PrepaidRenewed().get_email(
                    prepaid_object['number'],
                ),
                Notification.PrepaidRenewed().get_sms(
                    prepaid_object['number'],
                ),
            )

    @classmethod
    def prepaid_eighty_percent(cls, body):
        """
        Get notification from CGG on 80 percent usage of prepaid
        :param body:
        :type body:
        """
        prepaid_object = None
        body = Helper.get_dict_from_json(body)
        prepaid_serializer = NotifySubscriptionSerializer(
            data=body,
        )
        if prepaid_serializer.is_valid(raise_exception=True):
            prepaid_object = prepaid_serializer.data
        if prepaid_object is not None:
            send_notification_to_mis.delay(
                prepaid_object['customer_code'],
                Notification.PrepaidEighty().get_email_subject(),
                Notification.PrepaidEighty().get_email(
                    prepaid_object['number'],
                ),
                Notification.PrepaidEighty().get_sms(
                    prepaid_object['number'],
                ),

            )

    @classmethod
    def prepaid_max_usage(cls, body):
        """
        Get notification from CGG on max usage prepaid
        :param body:
        :type body:
        """
        prepaid_object = None
        body = Helper.get_dict_from_json(body)
        prepaid_serializer = NotifySubscriptionSerializer(
            data=body,
        )
        if prepaid_serializer.is_valid(raise_exception=True):
            prepaid_object = prepaid_serializer.data
        SubscriptionService.disable_outbound_calls(
            prepaid_object['subscription_code'],
            check_prepaid=True,
        )

        if prepaid_object is not None:
            send_notification_to_mis.delay(
                prepaid_object['customer_code'],
                Notification.PrepaidMaxUsage().get_email_subject(),
                Notification.PrepaidMaxUsage().get_email(
                    prepaid_object['number'],
                ),
                Notification.PrepaidMaxUsage().get_sms(
                    prepaid_object['number'],
                ),
            )

    @classmethod
    def get_runtime_configs(cls):
        """
        Get CGG Runtime configs
        """
        relative_uri = OcsConfiguration.URLs.RUNTIME_CONFIGS
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            http_method='get',
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def update_runtime_configs(cls, body):
        """
        Update CGG Runtime configs
        :param body:
        :type body:
        """
        relative_uri = OcsConfiguration.URLs.RUNTIME_CONFIGS
        url = CggService.cgg_url(relative_uri)
        response = CggService.cgg_response(
            url,
            http_method='patch',
            body=body,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_subscriptions(
            cls,
            customer_code=None,
            subscription_codes=None,
            bypass_pagination=False,
            force_reload=False,
    ):
        """
        Get list of subscriptions from CGG
        :param customer_code:
        :type customer_code:
        :param subscription_codes:
        :type subscription_codes:
        :param bypass_pagination:
        :type bypass_pagination:
        :param force_reload:
        :type force_reload:
        :return:
        :rtype:
        """
        response_type = CggService.ResponseType.LIST
        query_param = {}
        if bypass_pagination:
            query_param.update({
                'bypass_pagination': True
            })
            response_type = CggService.ResponseType.SINGLE
        if force_reload:
            query_param.update({
                'force_reload': True
            })
        body = {}
        if subscription_codes:
            body = {
                'subscription_codes': subscription_codes,
            }
        if customer_code is None:
            relative_url = OcsConfiguration.URLs.SUBSCRIPTIONS_ANTI
        else:
            relative_url = \
                OcsConfiguration.URLs.SUBSCRIPTIONS_WITH_CUSTOMER_ANTI
            relative_url = relative_url.format(
                cid=customer_code,
            )

        url = CggService.cgg_url(
            relative_url,
            query_param,
        )
        response = CggService.cgg_response(
            url,
            response_type=response_type,
            body=body,
        )

        return response

    @classmethod
    def get_subscription(
            cls,
            customer_code=None,
            subscription_code=None,
            force_reload=False,
    ):
        """
        Get a subscription from CGG
        :param customer_code:
        :type customer_code:
        :param subscription_code:
        :type subscription_code:
        :param force_reload:
        :type force_reload:
        :return:
        :rtype:
        """
        relative_url = ''
        if subscription_code is None:
            return api_exceptions.ValidationError400({
                'subscription_code': _("required field")
            })
        if customer_code is None and subscription_code is not None:
            relative_url = \
                OcsConfiguration.URLs.SUBSCRIPTION
            relative_url = relative_url.format(sid=subscription_code)
        elif customer_code is not None and subscription_code is not None:
            relative_url = OcsConfiguration.URLs.SUBSCRIPTION_WITH_CUSTOMER
            relative_url = relative_url.format(
                cid=customer_code,
                sid=subscription_code,
            )

        url = CggService.cgg_url(
            relative_url,
            {'force_reload': True} if force_reload else {},
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def deallocate_subscription(
            cls,
            subscription_code,
            body,
    ):
        """
        Deallocate subscription in CGG. This will disable the account in
        CGRateS as well
        :param subscription_code:
        :param body:
        :return:
        :rtype:
        """
        relative_url = OcsConfiguration.URLs.DEALLOCATE_SUBSCRIPTION
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url = CggService.cgg_url(relative_url)
        print(url)
        with(open('khosro_logx.txt','a')) as f:
            f.write(url)
            f.write('\n')
        response = CggService.cgg_response(
            url=url,
            http_method='post',
            body=body,
        )

        return response

    @classmethod
    def increase_credit_subscription(
            cls,
            subscription_code,
            body
    ):
        """
        Increase subscription's credit in CGG
        :param subscription_code:
        :type subscription_code:
        :param body:
        :type body:
        :return:
        :rtype:
        """
        relative_url = OcsConfiguration.URLs.CREDIT_SUBSCRIPTION
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url = CggService.cgg_url(relative_url)
        try:
            response = CggService.cgg_response(
                url=url,
                body=body,
                http_method='post'
            )
        except api_exceptions.APIException:
            raise

        return response

    @classmethod
    def increase_base_balance_subscription(
            cls,
            subscription_code,
            body
    ):
        """
        Increase subscription's base balance in CGG
        :param subscription_code:
        :type subscription_code:
        :param body:
        :type body:
        :return:
        :rtype:
        """
        relative_url = OcsConfiguration.URLs.BASE_BALANCE_SUBSCRIPTION
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            body=body,
            http_method='post'
        )

        return response

    @classmethod
    def debit_balance_subscription(
            cls,
            subscription_code,
            body
    ):
        """
        Debit subscription's current balance in CGRateS using CGG
        :param subscription_code:
        :type subscription_code:
        :param body:
        :type body:
        :return:
        :rtype:
        """
        relative_url = OcsConfiguration.URLs.SUBSCRIPTION_DEBIT_BALANCE
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            body=body,
            http_method='post'
        )

        return response

    @classmethod
    def add_balance_subscription(
            cls,
            subscription_code,
            body
    ):
        """
        Increase subscription's current balance in CGRateS using CGG
        :param subscription_code:
        :type subscription_code:
        :param body:
        :type body:
        :return:
        :rtype:
        """
        relative_url = OcsConfiguration.URLs.SUBSCRIPTION_ADD_BALANCE
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            body=body,
            http_method='post'
        )

        return response

    @classmethod
    def convert_subscription(
            cls,
            subscription_code,
            body
    ):
        """
        Convert a prepaid subscription to postpaid in CGG
        :param subscription_code:
        :type subscription_code:
        :param body:
        :type body:
        :return:
        :rtype:
        """
        relative_url = OcsConfiguration.URLs.CONVERT_SUBSCRIPTION
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url = CggService.cgg_url(relative_url)
        response = CggService.cgg_response(
            url=url,
            body=json.loads(body.decode('utf-8')),
            http_method='post'
        )

        return response

    @classmethod
    def remove_subscription(cls, subscription_code):
        """
        Remove a subscription from CGRateS Subscription
        :param subscription_code:
        :return:
        """
        relative_url = OcsConfiguration.URLs.SUBSCRIPTION
        relative_url = relative_url.format(
            sid=subscription_code,
        )
        url_subscription = CggService.cgg_url(relative_url)
        try:
            CggService.cgg_response(
                url=url_subscription,
                http_method='delete',
            )
        except api_exceptions.APIException:
            pass

        return True

    @classmethod
    def create_subscription(
            cls,
            customer_code,
            subscription_code,
            number,
            base_balance,
            package_id=None,
            used_balance=0,
            is_active=True,
            credit=0,
            is_prepaid=False,
    ):
        """
        Create new subscription in CGRateS Subscription
        :param is_prepaid:
        :param credit:
        :param customer_code:
        :param subscription_code:
        :param number:
        :param base_balance:
        :param package_id:
        :param used_balance:
        :param is_active:
        :return: boolean: True if successful, False otherwise
        """
        subscription_type = 'postpaid'
        if is_prepaid:
            subscription_type = 'prepaid'
        relative_url_subscriptions = OcsConfiguration.URLs.SUBSCRIPTIONS
        url_subscriptions = CggService.cgg_url(
            relative_url_subscriptions,
        )
        body_subscription = {
            "customer_code": customer_code,
            "subscription_code": subscription_code,
            "number": number,
            "base_balance": base_balance,
            "is_allocated": True,
            "is_active": is_active,
            "credit": credit,
            "subscription_type": subscription_type,
            "package_id": package_id,
        }
        body_debit = {
            "value": used_balance
        }
        if CggService.cgg_response(
                url=url_subscriptions,
                body=body_subscription,
                http_method='post'
        ):
            if used_balance > 0:
                return cls.debit_balance_subscription(
                    subscription_code,
                    body_debit,
                )
            else:
                return True

        return False

    @classmethod
    def update_subscription(
            cls,
            customer_code,
            subscription_code,
            base_balance=None,
            used_balance=None,
            credit=None,
            auto_pay=None,
    ):
        """
        Update a subscription in CGG
        :param customer_code:
        :type customer_code:
        :param subscription_code:
        :type subscription_code:
        :param base_balance:
        :type base_balance:
        :param used_balance:
        :type used_balance:
        :param credit:
        :type credit:
        :param auto_pay:
        :type auto_pay:
        :return:
        :rtype:
        """
        if subscription_code is None:
            raise api_exceptions.ValidationError400({
                "subscription_code": _("This field is required")
            })
        if customer_code is None:
            relative_url_subscriptions = OcsConfiguration.URLs.SUBSCRIPTION
            relative_url_subscriptions = relative_url_subscriptions.format(
                sid=subscription_code,
            )
        else:
            relative_url_subscriptions = \
                OcsConfiguration.URLs.SUBSCRIPTION_WITH_CUSTOMER
            relative_url_subscriptions = relative_url_subscriptions.format(
                cid=customer_code,
                sid=subscription_code,
            )
        url_update_subscriptions = CggService.cgg_url(
            relative_url_subscriptions,
        )
        body = {}
        if base_balance is not None:
            body.update(
                {
                    "base_balance": base_balance,
                }
            )
        if used_balance is not None:
            body.update(
                {
                    "used_balance": used_balance,
                }
            )
        if credit is not None:
            body.update(
                {
                    "credit": credit,
                }
            )
        if auto_pay is not None:
            body.update(
                {
                    "auto_pay": auto_pay,
                }
            )

        if CggService.cgg_response(
                url=url_update_subscriptions,
                body=body,
                http_method='patch'
        ):
            return True

        return False

    @classmethod
    def get_customers(
            cls,
            customer_codes=None,
            bypass_pagination=False,
    ):
        """
        Get all customers from CGG
        :param customer_codes:
        :type customer_codes:
        :param bypass_pagination:
        :type bypass_pagination:
        :return:
        :rtype:
        """
        response_type = CggService.ResponseType.LIST
        query_param = {}
        if bypass_pagination:
            query_param.update({
                'bypass_pagination': True
            })
            response_type = CggService.ResponseType.SINGLE

        if customer_codes:
            query_param.update({
                'customer_codes': ",".join(customer_codes)
            })

        relative_url = OcsConfiguration.URLs.CUSTOMERS
        url = CggService.cgg_url(
            relative_url,
            query_param,
        )
        response = CggService.cgg_response(
            url,
            response_type=response_type,
        )

        return response

    @classmethod
    def get_customer(
            cls,
            customer_code=None,
    ):
        """
        Get a customer from CGG
        :param customer_code:
        :type customer_code:
        :return:
        :rtype:
        """
        if customer_code is None:
            return api_exceptions.ValidationError400({
                'customer_code': _("required field")
            })

        relative_url = OcsConfiguration.URLs.CUSTOMER
        relative_url = relative_url.format(
            cid=customer_code,
        )
        url = CggService.cgg_url(
            relative_url,
        )
        response = CggService.cgg_response(
            url,
            response_type=CggService.ResponseType.SINGLE,
        )

        return response

    @classmethod
    def get_destinations(cls, query_params):
        """
        Get list of destinations
        :param query_params:
        :type query_params:
        """
        relative_url = OcsConfiguration.URLs.DESTINATIONS
        url = CggService.cgg_url(
            relative_url,
            query_params,
        )
        response = CggService.cgg_response(
            url=url,
            http_method='get',
            response_type=CggService.ResponseType.SINGLE if
            'bypass_pagination' in query_params else
            CggService.ResponseType.LIST,
        )

        return response
