import uuid
from datetime import datetime

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rspsrv.apps.membership.manager import UserManager, SessionManager
from rspsrv.apps.membership.versions.v1.configs import (
    MembershipConfiguration,
)
from rspsrv.tools.utility import RespinaBaseModel


class UserLoginStatus(object):
    UPPER_BOUND = 7
    UNKNOWN, OFFLINE, ONLINE, IDLE, DONT_DISTURB, BUSY, NOT_AVAILABLE = \
        range(UPPER_BOUND)


def get_session_expire_date():
    timezone.now() + timezone.timedelta(14)


class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    customer_code = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('customer')
        verbose_name_plural = _('customers')

    def __str__(self):
        return self.prime_code

    @property
    def prime_code(self):
        return "{}-{}".format(
            "prime",
            str(self.id).zfill(6),
        )


class User(RespinaBaseModel, AbstractBaseUser, PermissionsMixin):
    guid = models.UUIDField(default=uuid.uuid4)
    username = models.CharField(
        max_length=255,
        db_index=True,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,
    )
    user_type = models.CharField(
        max_length=128,
        null=False,
        choices=MembershipConfiguration.USER_TYPES,
        default=MembershipConfiguration.USER_TYPES[0][0],
    )
    email = models.EmailField(
        max_length=255,
        null=True,
        db_index=True,
    )
    mobile = models.CharField(
        max_length=16,
        null=True,
        db_index=True,
    )
    first_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    ascii_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )
    gender = models.CharField(
        max_length=8,
        choices=MembershipConfiguration.USER_GENDER,
        default=MembershipConfiguration.USER_GENDER[0][0],
    )
    job_title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    birthday = models.DateTimeField(null=True, blank=True)
    address = models.CharField(max_length=512, null=True, blank=True)
    # This field belongs to django, to remove it override some django :)
    is_staff = models.BooleanField(default=True)
    deleted = models.BooleanField(
        default=False,
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = [
        'mobile',
        'email',
    ]
    objects = UserManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('user')
        verbose_name_plural = _('users')
        constraints = [
            models.UniqueConstraint(
                fields=['mobile'],
                condition=Q(is_active=True),
                name='unique active mobile per user'
            ),
            models.UniqueConstraint(
                fields=['email'],
                condition=Q(is_active=True),
                name='unique active email per user'
            ),
        ]

    def __str__(self):
        return "{}{}".format(
            self.username,
            f" ({self.customer.prime_code})" if self.customer else "",
        )

    def get_full_name(self):
        if not self.first_name or not self.last_name:
            return self.username

        return ' '.join([self.first_name, self.last_name])

    def get_short_name(self):
        if not self.first_name:
            return self.username

        return self.first_name




class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=255)
    ip = models.GenericIPAddressField()
    expire_date = models.DateTimeField(default=get_session_expire_date)
    created_at = models.DateTimeField(default=timezone.now)

    objects = SessionManager()


class UserRecoverPasswordToken(models.Model):
    token = models.CharField(null=True, max_length=512)
    is_used = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=datetime.now)
