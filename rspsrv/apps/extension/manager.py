import logging

from django.db.models import Manager, QuerySet

logger = logging.getLogger("common")


class BaseExtensionManager(Manager):
    pass


class BaseExtensionQueryset(QuerySet):
    pass


ExtensionManger = BaseExtensionManager.from_queryset(BaseExtensionQueryset)

