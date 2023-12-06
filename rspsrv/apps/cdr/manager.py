from django.db.models import Manager, QuerySet


class BaseCDRManger(Manager):
    pass


class BaseCDRQueryset(QuerySet):
    pass


CDRManager = BaseCDRManger.from_queryset(BaseCDRQueryset)
