import html
import logging

from rspsrv.apps.cgg.versions.v1_0.tasks import send_notification_to_mis
from rspsrv.apps.extension.models import Extension
from rspsrv.apps.mis.versions.v1_0.config import Notification
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.cache import Cache
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class MigrateNotify:

    @classmethod
    def notify_migration(cls, number, prime_only):
        try:
            subscription_obj = Subscription.objects.get(
                number=Helper.normalize_number(number)
            )
        except Subscription.DoesNotExist:
            return

        customer_admin = Cache.get(
            'prime_migration',
            {
                'prime_code': subscription_obj.customer.prime_code,
            },
        )

        if customer_admin is None:
            return

        Cache.delete(
            'prime_migration',
            {
                'prime_code': subscription_obj.customer.prime_code,
            },
        )
        extensions = Extension.objects.filter(
            customer=subscription_obj.customer,
        )
        email_data = ""
        sms_data = ""
        for extension in extensions:
            email_data += f"<tr style='padding:0;'><td style='border: 1px " \
                          f"solid #000;margin: 0;padding: 5px;'>" \
                          f"&lrm;{extension.extension_number.number}</td>" \
                          f"<td style='border: 1px solid #000;margin: 0;" \
                          f"padding: 5px;'>&lrm;" \
                          f"{html.escape(extension.password)}" \
                          f"</td></tr>"
            sms_data += " "
        if prime_only:
            send_notification_to_mis.delay(
                customer_admin['id'],
                Notification.CustomerMigrationPrimeOnly().get_email_subject(),
                Notification.CustomerMigrationPrimeOnly().get_email(
                    customer_admin['prime_code'],
                    customer_admin['username'],
                    html.escape(customer_admin['password']),
                    email_data,
                ),
                Notification.CustomerMigrationPrimeOnly().get_sms(
                    customer_admin['prime_code'],
                    customer_admin['username'],
                    customer_admin['password'],
                    sms_data,
                ),
            )
        else:
            send_notification_to_mis.delay(
                customer_admin['id'],
                Notification.CustomerMigrationWithPro
                ().get_email_subject(),
                Notification.CustomerMigrationWithPro().get_email(
                    customer_admin['prime_code'],
                    customer_admin['username'],
                    html.escape(customer_admin['password']),
                ),
                Notification.CustomerMigrationWithPro().get_sms(
                    customer_admin['prime_code'],
                    customer_admin['username'],
                    customer_admin['password'],
                ),
            )
