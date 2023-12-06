from django.utils.translation import gettext_lazy as _
from model_utils import Choices


class Subscription:
    def __init__(self):
        pass

    class BaseBalancePayment:
        STATE_CHOICES = Choices(
            # (0, 'ready_to_pay', _('Ready to Pay')),
            (1, 'pending', _('Pending')),
            (2, 'paid', _('Paid')),
            (3, 'reject', _('Reject')),
        )
