from django.db.models import Manager, QuerySet


class BaseSubscriptionManager(Manager):
    def get_default(self, number):
        subscription = self.get(
            number=number,
            is_allocated=True,
        )

        return subscription


class BaseSubscriptionQuerySet(QuerySet):
    pass


SubscriptionManager = BaseSubscriptionManager.from_queryset(
    BaseSubscriptionQuerySet
)
