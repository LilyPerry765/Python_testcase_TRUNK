from django.db.models import QuerySet
from django.utils.translation import gettext as _


def batch(qs, size=100):
    if not isinstance(qs, QuerySet):
        raise TypeError(_('"qs" Argument Is not a QuerySet Object.'))

    total = qs.count()

    if not total:
        yield (qs.all(), 0, 0, 0)

    for start in range(0, total, size):
        end = min(start + size, total)

        yield (qs[start:end], start, end, total)
