from django.utils.translation import gettext as _
from rest_framework import exceptions

from rspsrv.apps.extension.models import ExtensionNumber
from rspsrv.apps.subscription.models import (
    Subscription,
    SUBSCRIPTION_TYPES,
)
from rspsrv.apps.subscription.versions.v1.serializers.subscription import (
    SubscriptionSerializer,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.cache import Cache


class SubscriptionService:

    @classmethod
    def disable_activation(
            cls,
            subscription_code,
    ):
        """
        Disable activation in subscription, return if check prepaid is True
        :param subscription_code:
        :type subscription_code:
        :return:
        :rtype:
        """
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
            )
        except Subscription.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        subscription_obj.activation = False
        subscription_obj.save()

        return True

    @classmethod
    def enable_activation(
            cls,
            subscription_code,
    ):
        """
        Enable activation in subscription, return if check prepaid is True
        :param subscription_code:
        :type subscription_code:
        :return:
        :rtype:
        """
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
            )
        except Subscription.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        subscription_obj.activation = True
        subscription_obj.save()

        return True

    @classmethod
    def disable_outbound_calls(
            cls,
            subscription_code,
            check_prepaid=False,
    ):
        """
        Disable allow_outbound in subscription, return if check prepaid is True
        :param subscription_code:
        :type subscription_code:
        :param check_prepaid:
        :type check_prepaid:
        :return:
        :rtype:
        """
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
            )
        except Subscription.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        if check_prepaid and subscription_obj.subscription_type != \
                SUBSCRIPTION_TYPES[1][0]:
            return False

        subscription_obj.allow_outbound = False
        subscription_obj.save()

        return True

    @classmethod
    def enable_outbound_calls(
            cls,
            subscription_code,
            check_prepaid=False,
    ):
        """
        Enable allow_outbound in subscription, return if check prepaid is True
        :param subscription_code:
        :type subscription_code:
        :param check_prepaid:
        :type check_prepaid:
        :return:
        :rtype:
        """
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
            )
        except Subscription.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        if check_prepaid and subscription_obj.subscription_type == \
                SUBSCRIPTION_TYPES[1][0]:
            return False

        subscription_obj.allow_outbound = True
        subscription_obj.save()

        return True

    @classmethod
    def get_outbound_calls_status(cls, subscription_code):
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
            )
        except Subscription.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        return bool(subscription_obj.allow_outbound)

    @classmethod
    def deallocate_subscription(cls, subscription_code):
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
                is_allocated=True,
            )
        except Subscription.DoesNotExist as e:
            raise exceptions.NotFound(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        subscription_obj.is_allocated = False
        subscription_obj.save()
        subscription_obj.subscription_extension.delete()
        ExtensionNumber.objects.filter(
            number=subscription_obj.number,
        ).delete()
        if subscription_obj.operator:
            subscription_obj.operator.is_active = False
            subscription_obj.operator.save()

        return subscription_obj

    @classmethod
    def get_customer_code_from_subscription(cls, subscription_code):
        customer_code = Cache.get(
            'customer_code',
            {
                "subscription_code": subscription_code,
            }
        )
        if customer_code is None:
            try:
                customer_code = Subscription.objects.get(
                    subscription_code=subscription_code,
                ).customer.customer_code
            except Subscription.DoesNotExist:
                raise
            Cache.set(
                'customer_code',
                {
                    "subscription_code": subscription_code,
                },
                customer_code,
            )

        return customer_code

    @classmethod
    def get_from_operator(cls, customer, operator):
        try:
            subscription_obj = Subscription.objects.get(
                is_allocated=True,
                operator=operator,
                customer=customer,
            )
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                _("Subscription does not exists")
            )

        return subscription_obj

    @classmethod
    def update_subscription(cls, subscription_id, data):
        try:
            subscription_obj = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                _("Subscription does not exists")
            )
        for key in (
                'max_call_concurrency',
                'allow_inbound',
                'allow_outbound',
                'activation',
                'international_call',
        ):
            setattr(
                subscription_obj,
                key,
                data.get(key, getattr(subscription_obj, key))
            )

        subscription_obj.save()

        if hasattr(subscription_obj, 'extension'):
            extension_obj = subscription_obj.extension
            for key in (
                    'status',
                    'forward_to',
                    'password',
            ):
                setattr(
                    extension_obj,
                    key,
                    data.get(key, getattr(extension_obj, key))
                )
            extension_obj.save()

        subscription_srz = SubscriptionSerializer(
            subscription_obj
        )

        return subscription_srz.data
