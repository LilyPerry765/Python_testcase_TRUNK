import logging

from django.conf import settings

from rspsrv.apps.mis.versions.v1_0.config import (
    Notification,
)
from rspsrv.apps.mis.versions.v1_0.services.mis import MisService
from rspsrv.tools import api_exceptions
from rspsrv.tools.permissions import (
    Group,
)

logger = logging.getLogger("common")


class RecoverEmail:
    @staticmethod
    def send_recover_email(user, token):
        """
        Send recover email through MIS
        :param user:
        :param token:
        :return:
        """
        if Group.CUSTOMER_ADMIN in user.groups.all().values_list(
                'name',
                flat=True,
        ):
            recover_url = '{base_url}/{relative_url}/?token={token}'.format(
                base_url=
                settings.DASHBOARD_REDIRECT_ABSOLUTE.strip("/"),
                relative_url=
                settings.RESET_PASSWORD_REDIRECT_RELATIVE.strip("/"),
                token=token,
            )
            subscriptions = user.customer.subscriptions.all()
            if len(subscriptions) == 0:
                raise
            try:
                MisService.send_notification(
                    customer_code=user.customer.customer_code,
                    email_subject=
                    Notification.PasswordRecovery().get_email_subject(),
                    email_content=
                    Notification.PasswordRecovery().get_email(
                        recover_url,
                    ),
                    sms_content=
                    Notification.PasswordRecovery().get_sms(
                        recover_url,
                    ),
                )
            except api_exceptions.APIException:
                raise
        else:
            recover_url = '{base_url}/{relative_url}/?token={token}'.format(
                base_url=
                settings.DASHBOARD_RESPINA_REDIRECT_ABSOLUTE.strip("/"),
                relative_url=
                settings.RESET_PASSWORD_REDIRECT_RELATIVE.strip("/"),
                token=token,
            )
            try:
                MisService.send_notification(
                    email=user.email,
                    mobile=user.mobile,
                    email_subject=
                    Notification.PasswordRecovery().get_email_subject(),
                    email_content=
                    Notification.PasswordRecovery().get_email(
                        recover_url,
                    ),
                    sms_content=
                    Notification.PasswordRecovery().get_sms(
                        recover_url,
                    ),
                )
            except api_exceptions.APIException:
                raise
