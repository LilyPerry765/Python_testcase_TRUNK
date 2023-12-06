from django.db.models import Manager, QuerySet


class BasePaymentManger(Manager):
    pass


class BasePaymentQueryset(QuerySet):
    pass


class BaseTransactionManger(Manager):
    pass


class BaseTransactionQueryset(QuerySet):
    pass


PaymentManager = BasePaymentManger.from_queryset(BasePaymentQueryset)
TransactionManager = BaseTransactionManger.from_queryset(BaseTransactionQueryset)
