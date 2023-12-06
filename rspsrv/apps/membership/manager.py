import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.db.models import Manager

from rspsrv.apps.membership.versions.v1.configs import (
    MembershipConfiguration,
)


class NexfonUserManager(BaseUserManager):
    def create_user(
            self,
            username,
            customer,
            email,
            mobile,
            ascii_name=None,
            user_type=MembershipConfiguration.USER_TYPES[0][0],
            gender=MembershipConfiguration.USER_GENDER[0][0],
            job_title=None,
            address=None,
            birthday=None,
            is_active=True,
            deleted=False,
            first_name=None,
            last_name=None,
            password=None,
            groups=None,
    ):
        """
        Creates and saves a User
        """
        user = self.model(
            guid=uuid.uuid4(),
            username=username,
            customer=customer,
            mobile=mobile,
            first_name=first_name,
            last_name=last_name,
            ascii_name=ascii_name,
            email=self.normalize_email(email),
            gender=gender,
            job_title=job_title,
            address=address,
            birthday=birthday,
            is_active=is_active,
            deleted=deleted,
            user_type=user_type,
        )

        user.set_password(password)
        user.save(using=self._db)
        if groups:
            user.groups.set(groups)

        return user

    def create_superuser(
            self,
            username,
            email,
            password,
            mobile,
    ):
        user = self.create_user(
            customer=None,
            username=username,
            email=email,
            password=password,
            mobile=mobile,
        )
        user.is_superuser = True
        user.save(using=self._db)

        return user


class BaseUserQuerySet(models.QuerySet):
    pass


class BaseSessionManager(Manager):
    pass


class BaseSessionQuerySet(models.QuerySet):
    pass


UserManager = NexfonUserManager.from_queryset(BaseUserQuerySet)
SessionManager = BaseSessionManager.from_queryset(BaseSessionQuerySet)
