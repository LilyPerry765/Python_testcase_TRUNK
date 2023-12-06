# --------------------------------------------------------------------------
# To use notification on any languages pass the `lang` argument to get_sms,
# get_email or get_email_subject methods of each class
# (C) 2020 MehrdadEP, Tehran, Iran
# Respina Networks and beyonds - __init__.py
# Created at 2020-8-11,  14:20:38
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import codecs
import os

from django.conf import settings

from rspsrv.tools.cache import Cache


class Notification:
    class BaseNotification:
        path = ''

        def __init__(self):
            if self.get_email_subject() is None:
                load_templates()

        def get_email_subject(self, **kwargs):
            raise NotImplementedError

        def get_sms(self, **kwargs):
            raise NotImplementedError

        def get_email(self, **kwargs):
            raise NotImplementedError

        @classmethod
        def get_path(cls, ):
            return cls.path

    class AutoPayInterim(BaseNotification):
        path = 'auto_pay_interim'

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_sms(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

        def get_email(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

    class AutoPayPeriodic(BaseNotification):
        path = 'auto_pay_periodic'

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_sms(self, number, total_cost, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
            )

        def get_email(self, number, total_cost, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
            )

    class PostpaidMaxUsage(BaseNotification):
        path = 'postpaid_max'

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class PrepaidMaxUsage(BaseNotification):
        path = 'prepaid_max'

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class PrepaidEighty(BaseNotification):
        path = 'prepaid_eighty'

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class PrepaidExpired(BaseNotification):
        path = 'prepaid_expired'

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class PrepaidRenewed(BaseNotification):
        path = 'prepaid_renewed'

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class DueDateWarning1(BaseNotification):
        path = 'due_date_warning_1'

        def get_sms(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

    class DueDateWarning2(BaseNotification):
        path = 'due_date_warning_2'

        def get_sms(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

    class DueDateWarning3(BaseNotification):
        path = 'due_date_warning_3'

        def get_sms(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

    class DueDateWarning4(BaseNotification):
        path = 'due_date_warning_4'

        def get_sms(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

    class InterimInvoice(BaseNotification):
        path = 'interim_invoice'

        def get_sms(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, total_cost, cause, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
                cause=cause,
            )

    class PeriodicInvoice(BaseNotification):
        path = "periodic_invoice"

        def get_sms(self, number, total_cost, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, total_cost, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
                total_cost=total_cost,
            )

    class PasswordRecovery(BaseNotification):
        path = "password_recovery"

        def get_sms(self, recover_url, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                recover_url=recover_url,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, recover_url, lang='fa'):
            return Cache.get(
                self.path,
                {"type": "email", "lang": lang}
            ).format(recover_url=recover_url)

    class DeallocationWarning1(BaseNotification):
        path = "deallocation_warning_1"

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class DeallocationWarning2(BaseNotification):
        path = "deallocation_warning_2"

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class DeallocationManual(BaseNotification):
        path = "deallocation_manual"

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class ConvertPrepaid(BaseNotification):
        path = "convert_prepaid"

        def get_sms(self, number, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                number=number,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, number, lang='fa'):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                number=number,
            )

    class CustomerMigrationWithPro(BaseNotification):
        path = "customer_migration_with_pro"

        def get_sms(
                self,
                prime_code,
                username,
                password,
                lang='fa',
        ):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                prime_code=prime_code,
                username=username,
                password=password,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(
                self,
                prime_code,
                username,
                password,
                lang='fa',
        ):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                prime_code=prime_code,
                username=username,
                password=password,
            )

    class CustomerMigrationPrimeOnly(BaseNotification):
        path = "customer_migration_prime_only"

        def get_sms(
                self,
                prime_code,
                username,
                password,
                extra_data,
                lang='fa',
        ):
            return Cache.get(self.path, {"type": "sms", "lang": lang}).format(
                prime_code=prime_code,
                username=username,
                password=password,
                extra_data=extra_data,
            )

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(
                self,
                prime_code,
                username,
                password,
                extra_data,
                lang='fa',
        ):
            return Cache.get(self.path,
                             {"type": "email", "lang": lang}).format(
                prime_code=prime_code,
                username=username,
                password=password,
                extra_data=extra_data,
            )

    class MFAMessage(BaseNotification):
        path = "one_time_token"

        def get_sms(self, lang='fa'):
            return Cache.get(self.path, {"type": "sms", "lang": lang})

        def get_email_subject(self, lang='fa'):
            return Cache.get(self.path, {"type": "subject", "lang": lang})

        def get_email(self, lang='fa'):
            return Cache.get(self.path, {"type": "email", "lang": lang})


def load_templates():
    base_path = settings.NOTIFICATION_TEMPLATE_PATH
    if base_path is None:
        raise ValueError("NOTIFICATION_TEMPLATE_PATH can not be empty")

    for c in [
        Notification.PostpaidMaxUsage,
        Notification.PrepaidMaxUsage,
        Notification.PrepaidEighty,
        Notification.AutoPayPeriodic,
        Notification.AutoPayInterim,
        Notification.PrepaidExpired,
        Notification.PrepaidRenewed,
        Notification.DueDateWarning1,
        Notification.DueDateWarning2,
        Notification.DueDateWarning3,
        Notification.DueDateWarning4,
        Notification.InterimInvoice,
        Notification.PeriodicInvoice,
        Notification.PasswordRecovery,
        Notification.DeallocationWarning1,
        Notification.DeallocationWarning2,
        Notification.DeallocationManual,
        Notification.ConvertPrepaid,
        Notification.CustomerMigrationWithPro,
        Notification.CustomerMigrationPrimeOnly,
        Notification.MFAMessage,
    ]:
        load_template(base_path, c.get_path())


def load_template(base_path, name):
    languages = [item for item in os.listdir(base_path) if
                 os.path.isdir(os.path.join(base_path, item))]

    for lang in languages:
        email_path = os.path.join(base_path, lang, 'email')
        subject_path = os.path.join(base_path, lang, 'subject')
        sms_path = os.path.join(base_path, lang, 'sms')
        sms_content = read_file(
            os.path.join(sms_path, name)
        )
        subject_content = read_file(
            os.path.join(subject_path, name)
        )
        email_content = read_file(
            os.path.join(email_path, name)
        )
        Cache.set(
            name,
            {
                "type": "sms",
                "lang": lang,
            },
            sms_content,
        )
        Cache.set(
            name,
            {
                "type": "subject",
                "lang": lang,
            },
            subject_content,
        )
        Cache.set(
            name,
            {
                "type": "email",
                "lang": lang,
            },
            email_content,
        )


def read_file(path):
    try:
        with codecs.open(path, 'r') as f:
            content = f.read()
    except Exception:
        raise

    return content


class MisConfigurations:
    class URIs:
        GET_ACCOUNT_INFO = "/api/Nexfon/GetaccountInfo?SubScriptionId={sub_id}"
        GET_CUSTOMER_INFO = "api/Nexfon/GetCustomerID?SubID={sub_id}"
        SEND_EMAIL = "api/Nexfon/SendEmail"
        SEND_SMS = "api/Nexfon/SendSms"
