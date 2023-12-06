from django.conf import settings

from rspsrv.apps.membership.models import Customer, User
from rspsrv.apps.membership.versions.v1.configs import MembershipConfiguration
from rspsrv.apps.membership.versions.v1.serializers.customer import (
    CustomerSerializer,
)
from rspsrv.apps.membership.versions.v1.serializers.user import UserSerializer
from rspsrv.apps.membership.versions.v1.services.user import UserService
from rspsrv.apps.subscription.models import Subscription
from rspsrv.tools import api_exceptions
from rspsrv.tools.cache import Cache
from rspsrv.tools.permissions import Group as GroupPermission


class CustomerService:
    @classmethod
    def create_or_get_default_user(cls, customer_code):
        """
        Get default user for a customer or create a new one
        :param customer_code:
        :return:
        """
        if User.objects.filter(
                customer__customer_code=customer_code,
                username=settings.CRM_APP.DEFAULT_CUSTOMER_ADMIN_USERNAME,
        ).exists():
            user = User.objects.get(
                customer__customer_code=customer_code,
                username=settings.CRM_APP.DEFAULT_CUSTOMER_ADMIN_USERNAME,
            )
            user_serializer = UserSerializer(user)
            user_data = user_serializer.data
            user_data['password'] = None
            return user_data
        else:
            params = {
                'customer_code': customer_code,
                'username': settings.CRM_APP.DEFAULT_CUSTOMER_ADMIN_USERNAME,
                'user_type': MembershipConfiguration.USER_TYPES[1][0],
                'group': GroupPermission.CUSTOMER_ADMIN,
            }

            return UserService.create_user(params, False)

    @classmethod
    def create_customer(cls, customer_code):
        try:
            customer = Customer.objects.get(
                customer_code=customer_code,
            )
            customer = CustomerSerializer(customer)
        except Customer.DoesNotExist:
            customer = CustomerSerializer(
                data={
                    "customer_code": customer_code,
                },
            )

            if not customer.is_valid():
                raise api_exceptions.ValidationError400(customer.errors)

            customer.save()

        return customer.data

    @classmethod
    def get_customer_code_from_id(cls, customer_id):
        customer_code = Cache.get(
            'customer_code',
            {
                "customer_id": customer_id,
            }
        )
        if customer_code is None:
            try:
                customer_code = Customer.objects.get(
                    id=customer_id,
                ).customer_code
            except Customer.DoesNotExist:
                raise
            Cache.set(
                'customer_code',
                {
                    "customer_id": customer_id,
                },
                customer_code,
            )

        return customer_code

    @classmethod
    def get_subscription_code(cls, customer_id):
        subscriptions = Subscription.objects.filter(
            customer__id=customer_id,
            is_allocated=True,
        )[:1]

        if len(subscriptions):
            return subscriptions[0].subscription_code

        return None
