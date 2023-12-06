import logging

from django.conf import settings

logger = logging.getLogger("common")


class ExtensionService:
    @staticmethod
    def is_parent(subscription, extension, **kwargs):
        if subscription + settings.APPS['extension']['default_parent_extension_suffix'] == extension:
            return True

        return False

    @staticmethod
    def is_child(subscription, extension, **kwargs):
        if subscription + settings.APPS['extension']['default_parent_extension_suffix'] != extension:
            return True

        return False
