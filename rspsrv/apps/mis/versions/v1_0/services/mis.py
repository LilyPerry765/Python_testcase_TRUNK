# --------------------------------------------------------------------------
# Handle notification sending through MIS
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - mis.py
# Created at 2020-6-29,  9:12:48
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------
import logging

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from rspsrv.apps.mis.versions.v1_0.config import MisConfigurations
from rspsrv.apps.mis.versions.v1_0.serializers.mis import ClientInfoTransformer
from rspsrv.tools import api_exceptions
from rspsrv.tools.cache import Cache

logger = logging.getLogger("common")


class MisService:
    @staticmethod
    def get_mobile(subscription_code):
        """
        Return a mobile number related to the subscription
        :param subscription_code:
        :return:
        """
        data = MisService.get_client_info(subscription_code)
        if data['natural_person']:
            return data['natural_person']['nexfon']['mobile']
        else:
            return data['incorporation']['nexfon']['mobile']

    @staticmethod
    def get_client_info(subscription_code):
        data = Cache.get(
            'customer_info',
            {
                "subscription_code": str(subscription_code),
            }
        )
        if not data:
            url = "{base_url}/{relative_url}".format(
                base_url=settings.MIS.API.BASE_URL.strip("/"),
                relative_url=MisConfigurations.URIs.GET_ACCOUNT_INFO.format(
                    sub_id=subscription_code,
                ).strip("/"),
            )
            try:
                response = requests.get(
                    url,
                    headers={
                        'Authorization': settings.MIS.API.KEY,
                    },
                )
            except Exception as e:
                raise api_exceptions.APIException(detail=str(e))

            if not status.is_success(response.status_code):
                raise api_exceptions.raise_exception(
                    status_code=response.status_code
                )
            data = ClientInfoTransformer.from_raw(response.json() or {})
            Cache.set(
                'customer_info',
                {
                    "subscription_code": str(subscription_code),
                },
                data,
                settings.CRM_APP.CACHE_EXPIRY,
            )

        return data

    @staticmethod
    def get_customer_code(sub_id):
        url = "{base_url}/{relative_url}".format(
            base_url=settings.MIS.API.BASE_URL.strip("/"),
            relative_url=MisConfigurations.URIs.GET_CUSTOMER_INFO.format(
                sub_id=sub_id,
            ),
        )
        try:
            response = requests.get(
                url,
                headers={
                    'Authorization': settings.MIS.API.KEY,
                },
            )
        except Exception as e:
            raise api_exceptions.APIException(detail=str(e))

        if not status.is_success(response.status_code):
            raise api_exceptions.raise_exception(
                status_code=response.status_code
            )

        data = response.json()

        return data

    @staticmethod
    def send_notification(
            email_subject,
            email_content,
            sms_content,
            customer_code=None,
            email=None,
            mobile=None,
    ):
        """
        Send notification to users through MIS
        (Never fill both subscription_id and (email+mobile) at the same time)
        :param email_content: html formatted text
        :param email_subject: plain text
        :param sms_content: plain text
        :param customer_code:
        :param email:
        :param mobile:
        :return:
        """
        # Sorry, This is to the ridiculous API design of CRM
        default_account_id = settings.MIS.DEFAULT_ACCOUNT_ID
        sms_api = "{base_url}/{relative_url}/".format(
            base_url=settings.MIS.API.BASE_URL.strip("/"),
            relative_url=MisConfigurations.URIs.SEND_SMS.strip("/"),
        )
        email_api = "{base_url}/{relative_url}/".format(
            base_url=settings.MIS.API.BASE_URL.strip("/"),
            relative_url=MisConfigurations.URIs.SEND_EMAIL.strip("/"),
        )

        if customer_code:
            sms_params = {
                "AccountId": customer_code,
                "PhoneNumber": "",
                "Message": sms_content
            }
            email_params = {
                "AccountId": customer_code,
                "Email": "",
                "Message": email_content,
                "subject": email_subject,
            }
        else:
            sms_params = {
                "AccountId": default_account_id,
                "PhoneNumber": mobile,
                "Message": sms_content
            }
            email_params = {
                "AccountId": default_account_id,
                "Email": email,
                "Message": email_content,
                "subject": email_subject,
            }

        try:
            sms_res = requests.post(
                sms_api,
                json=sms_params,
                headers={
                    'Authorization': settings.MIS.API.KEY,
                },
            )
        except Exception as e:
            logger.error("MIS send sms failed - params: {} error: {}".format(
                sms_params,
                str(e)
            ))
            raise api_exceptions.APIException(
                _("Failed to send sms")
            )

        try:
            email_res = requests.post(
                email_api,
                json=email_params,
                headers={
                    'Authorization': settings.MIS.API.KEY,
                },
            )
        except Exception as e:
            logger.error(
                "MIS send email failed - to: {} subject: {} error: {}".format(
                    email if email else customer_code,
                    email_subject,
                    str(e)
                ))
            raise api_exceptions.APIException(
                _("Failed to send email")
            )

        if sms_res and not status.is_success(sms_res.status_code):
            logger.error(
                "MIS send sms failed - params: {} error: {}".format(
                    sms_params,
                    str(sms_res.content)
                )
            )

        if email_res and not status.is_success(email_res.status_code):
            logger.error(
                "MIS send email failed - to: {} subject: {} error: {}".format(
                    email if email else customer_code,
                    email_subject,
                    str(email_res.content)
                ))
