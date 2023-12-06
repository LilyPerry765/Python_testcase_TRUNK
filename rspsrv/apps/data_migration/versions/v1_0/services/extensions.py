import logging

from django.conf import settings

from rspsrv.apps.crm.services.v3.dispatcher import DispatcherService
from rspsrv.apps.extension.models import Extension, ExtensionNumber
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class ImportExtensions:
    @classmethod
    def import_extension_numbers(cls, numbers):
        for number in numbers:
            del number['id']
            number['number'] = Helper.normalize_number(
                number['number'],
            )
            ExtensionNumber.objects.create(**number)

        return

    @classmethod
    def import_extensions(cls, extensions):
        for extension in extensions:
            try:
                subscription_obj = Subscription.objects.get(
                    number=Helper.normalize_number(
                        extension['gateway_main_number'],
                    )
                )
            except Subscription.DoesNotExist:
                subscription_obj = None

            extension['callerid'] = Helper.normalize_number(
                extension['callerid'],
            )
            extension['subscription_id'] = None
            extension['customer_id'] = None
            extension['password'] = Helper.extension_password()
            if subscription_obj:
                extension['subscription_id'] = subscription_obj.id
                extension['customer_id'] = subscription_obj.customer.id

            try:
                extension['extension_number_id'] = ExtensionNumber.objects.get(
                    number=Helper.normalize_number(
                        extension['extension_number'],
                    )
                ).id
            except ExtensionNumber.DoesNotExist:
                extension['extension_number_id'] = None
            del extension['id']
            del extension['gateway_main_number']
            del extension['extension_number']
            del extension['business_week_id']
            del extension['conditional_list_id']
            del extension['user_id']
            extension_obj = Extension.objects.create(**extension)
            Extension.objects.filter(id=extension_obj.id).update(
                updated_at=extension['updated_at'],
                created_at=extension['created_at']
            )

            if not settings.IGNORE_CREATION_FLOW:
                try:
                    DispatcherService.remove_dispatch(
                        extension_obj.subscription.number,
                    )
                except Exception:
                    pass
                try:
                    DispatcherService.new_dispatch(
                        extension_obj.subscription.number,
                    )
                except Exception as e:
                    logger.error(e)
