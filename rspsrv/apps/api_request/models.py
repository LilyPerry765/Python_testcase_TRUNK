import uuid

from django.db import models
from jsonfield import JSONField

from rspsrv.apps.membership.models import User

choices_http_methods = (
    ('option', 'option'),
    ('get', 'get'),
    ('post', 'post'),
    ('put', 'put'),
    ('delete', 'delete'),
    ('patch', 'patch'),
)

choices_direction_types = (
    ('in', 'in'),
    ('out', 'out'),
)


class APIRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    direction = models.CharField(
        max_length=8,
        choices=choices_direction_types,
        null=False,
        blank=False,
        default=choices_direction_types[0][0]
    )
    app_name = models.CharField(max_length=128, null=False, blank=False)
    label = models.CharField(max_length=128, null=False, blank=False)
    ip = models.CharField(max_length=128, null=True, blank=True)
    http_method = models.CharField(
        max_length=8,
        choices=choices_http_methods,
        null=False, blank=False,
    )
    uri = models.CharField(max_length=1024, null=False, blank=False)
    status_code = models.SmallIntegerField(null=False, blank=False)
    request = JSONField(null=True, blank=True)
    response = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
