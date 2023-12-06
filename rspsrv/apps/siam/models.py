import uuid

from django.db import models
from django.utils.translation import gettext as _

choices_susp_id = (
    (0, _('siam.suspend')),
    (1, _('siam.release')),
)

choices_susp_type = (
    (2, _('siam.suspend_type.bidirectional')),
)

choices_susp_order = (
    ('3940000', _('siam.suspend_order.release')),
)


class SuspendHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    subscription_code = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )
    number = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )
    susp_id = models.SmallIntegerField(
        null=False,
        blank=False,
        choices=choices_susp_id,
    )
    susp_type = models.SmallIntegerField(
        null=False,
        blank=False,
        choices=choices_susp_type,
    )
    susp_order = models.CharField(
        max_length=16,
        choices=choices_susp_order,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NumberingCapacity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    ASR1 = models.FloatField(
        null=False,
        blank=False
    )
    CER2 = models.FloatField(
        null=False,
        blank=False
    )
    ASR3 = models.FloatField(
        null=False,
        blank=False
    )
    POI4 = models.FloatField(
        null=False,
        blank=False
    )
    ASR5_land = models.FloatField(
        null=False,
        blank=False
    )
    ASR5_cell = models.FloatField(
        null=False,
        blank=False
    )
    ASR6 = models.FloatField(
        null=False,
        blank=False
    )
    CER7 = models.FloatField(
        null=False,
        blank=False
    )
    ABR8_land = models.FloatField(
        null=False,
        blank=False
    )
    ABR8_cell = models.FloatField(
        null=False,
        blank=False
    )
    ASR9_land = models.FloatField(
        null=False,
        blank=False
    )
    ASR9_cell = models.FloatField(
        null=False,
        blank=False
    )
    odate = models.DateField(
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
