from django.db.models import Manager, QuerySet


class BaseEndpointManger(Manager):
    pass


class BaseEndpointQueryset(QuerySet):
    pass


class BaseBrandManager(Manager):
    pass


class BaseBrandQuerySet(QuerySet):
    pass


class BaseEndpointOptionManager(Manager):
    pass


class BaseEndpointOptionQuerySet(QuerySet):
    pass


class BaseBrandOptionManager(Manager):
    pass


class BaseBrandOptionQuerySet(QuerySet):
    pass


EndpointManager = BaseEndpointManger.from_queryset(BaseEndpointQueryset)
BrandManager = BaseBrandManager.from_queryset(BaseBrandQuerySet)
EndpointOptionManager = BaseEndpointOptionManager.from_queryset(
    BaseEndpointOptionQuerySet
)
BrandOptionManager = BaseBrandOptionManager.from_queryset(
    BaseBrandOptionQuerySet
)
