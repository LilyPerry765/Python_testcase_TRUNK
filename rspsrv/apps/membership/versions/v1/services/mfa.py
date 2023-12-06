import requests
from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import status, exceptions

from rspsrv.apps.membership.versions.v1.configs import MFAConfig
from rspsrv.apps.mis.versions.v1_0.config import Notification
from rspsrv.tools import api_exceptions


class MFAService:
    @classmethod
    def mfa_response(
            cls,
            relative_url,
            body=None,
            http_method='get',
    ):
        """
        A generic method to send requests to MFA service
        :param relative_url:
        :param body:
        :param http_method:
        :return:
        """
        if body is None:
            body = {}
        url = "{}/{}/".format(
            settings.MFA_SERVICE['api_url'].strip("/"),
            relative_url.strip("/"),
        )
        headers = {
            'Content-type': 'application/json',
            'Authorization': settings.MFA_SERVICE['auth_token']
        }

        try:
            if http_method in ('patch', 'post'):
                requests_rest_method = getattr(requests, http_method)
                r = requests_rest_method(
                    url=url,
                    json=body,
                    headers=headers,
                    timeout=5.0,
                )
            elif http_method == 'delete':
                r = requests.delete(
                    url=url,
                    headers=headers,
                    timeout=5.0,
                )
            else:
                r = requests.get(
                    url=url,
                    json=body,
                    headers=headers,
                    timeout=5.0,
                )
        except requests.exceptions.Timeout:
            raise api_exceptions.RequestTimeout408(
                detail="Timeout on connection to {}".format(url)
            )
        except exceptions.APIException:
            raise

        if status.is_success(r.status_code):
            return True
        elif r.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            raise exceptions.Throttled(
                detail=_(
                    "A generate token request is submitted recently, "
                    "try again in a while",
                )
            )
        return False

    @classmethod
    def validate(cls, mobile, token):
        """
        Check for the validation of a token using MFA service
        :param mobile:
        :param token:
        :return:
        """
        body = {
            "name": settings.MFA_SERVICE['consumer_name'],
            "mobile": mobile,
            "token": token,
        }

        return cls.mfa_response(
            relative_url=MFAConfig.URLs.VALIDATE,
            body=body,
            http_method='post',
        )

    @classmethod
    def generate(cls, mobile):
        """
        Generate and send one time token using MFA service
        :param mobile:
        :return:
        """
        body = {
            "name": settings.MFA_SERVICE['consumer_name'],
            "sms": {
                "to": mobile,
                "message": Notification.MFAMessage().get_sms(),
            }
        }

        return cls.mfa_response(
            relative_url=MFAConfig.URLs.GENERATE,
            body=body,
            http_method='post',
        )
