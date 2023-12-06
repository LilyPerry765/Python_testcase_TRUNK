import logging

from django.db import transaction
from django.http import QueryDict
from django.utils.translation import gettext as _
from rest_framework import exceptions

from rspsrv.apps.cgg.versions.v1_0.tasks import (
    send_notification_to_mis_with_subscription,
)
from rspsrv.apps.crm.serializers.v3.product_serializers import (
    ProductEmpowerSerializer,
    ProductUpdateSerializer,
    SubscriptionCreateSerializer,
)
from rspsrv.apps.extension.forms import ExtensionModelForm
from rspsrv.apps.extension.models import Extension
from rspsrv.apps.mis.versions.v1_0.config import Notification
from rspsrv.apps.ocs.versions.v1_0.services.ocs import OcsService
from rspsrv.apps.subscription.models import Subscription, SUBSCRIPTION_TYPES
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)
from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class ProductService:

    @classmethod
    @transaction.atomic
    def change_product_activation(cls, subscription_code, params):
        empower = ProductEmpowerSerializer(
            data=params
        )
        if empower.is_valid(raise_exception=True):
            empower = empower.data
            try:
                subscription_obj = Subscription.objects.get(
                    subscription_code=subscription_code,
                    is_allocated=True,
                )
            except Subscription.DoesNotExist as e:
                raise api_exceptions.NotFound404(detail=e)
            except Subscription.MultipleObjectsReturned as e:
                raise api_exceptions.Conflict409(detail=e)

            subscription_obj.activation = empower['activation']
            subscription_obj.allow_inbound = empower['inbound']
            subscription_obj.allow_outbound = empower['outbound']
            subscription_obj.save()

            if subscription_obj.operator:
                subscription_obj.operator.is_active = empower['activation']
                subscription_obj.operator.save()

            return subscription_obj

    @classmethod
    def activate_pro(cls, subscription_code):
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
                is_allocated=True,
            )
        except Subscription.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        try:
            extension_obj = Extension.objects.get(
                extension_number__number=subscription_obj.number,
            )
        except Extension.DoesNotExist as e:
            raise api_exceptions.NotFound404(detail=e)

        extension_obj.has_pro = True
        extension_obj.save()

        return True

    @classmethod
    @transaction.atomic
    def update_product(cls, params, subscription_code):
        product_update_serializer = ProductUpdateSerializer(
            data=params
        )
        try:
            product_update_serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError:
            raise
        validated_data = product_update_serializer.validated_data
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
                is_allocated=True,
            )
        except (
                Subscription.DoesNotExist,
                Subscription.MultipleObjectsReturned,
        ) as e:
            raise exceptions.NotFound(detail=e)

        subscription_obj.latitude = validated_data.get(
            'latitude',
            subscription_obj.latitude
        )
        subscription_obj.longitude = validated_data.get(
            'longitude',
            subscription_obj.longitude
        )
        subscription_obj.ip = validated_data.get(
            'ip',
            subscription_obj.ip
        )
        subscription_obj.max_call_concurrency = validated_data.get(
            'max_call_concurrency',
            subscription_obj.max_call_concurrency
        )

        subscription_obj.save()

        OcsService.update_subscription(
            customer_code=subscription_obj.customer.id,
            subscription_code=subscription_obj.subscription_code,
            base_balance=validated_data.get(
                'base_balance',
            ),
            used_balance=validated_data.get(
                'used_balance',
                0
            )
        )

        return subscription_obj

    @classmethod
    def create_subscription(cls, params):
        subscription_type = SUBSCRIPTION_TYPES[0][0]
        is_prepaid = False
        if 'is_prepaid' in params:
            is_prepaid = params.pop('is_prepaid')
        if is_prepaid:
            subscription_type = SUBSCRIPTION_TYPES[1][0]

        subscription_srz = SubscriptionCreateSerializer(
            data=params
        )

        if not subscription_srz.is_valid():
            raise api_exceptions.ValidationError400(subscription_srz.errors)

        subscription_srz = subscription_srz.data
        subscription_obj = Subscription(
            subscription_type=subscription_type,
            subscription_code=subscription_srz['subscription_code'],
            number=subscription_srz['number'],
            customer_id=subscription_srz['customer_id'],
            international_call=False,
            destination_type='extension',
            destination_number=subscription_srz['destination_number'],
            destination_type_off='end',
            max_call_concurrency=subscription_srz['max_call_concurrency'],
            outbound_min_length=1,
            latitude=subscription_srz['latitude'],
            longitude=subscription_srz['longitude'],
            ip=subscription_srz['ip'],
        )
        subscription_obj.save()

        if not OcsService.create_subscription(
                subscription_srz['customer_id'],
                subscription_srz['subscription_code'],
                subscription_srz['number'],
                subscription_srz['base_balance'],
                subscription_srz['package_id'],
                is_prepaid=is_prepaid,
        ):
            raise exceptions.APIException(
                _("Can not create subscription in CGG")
            )

        return subscription_obj

    @classmethod
    def create_extension(cls, params):
        query_dict_params = QueryDict(mutable=True)
        query_dict_params.update(params)

        form = ExtensionModelForm(params)

        if not form.is_valid():
            raise exceptions.ValidationError(detail=form.error_list)

        extension = form.save()

        return extension

    @classmethod
    @transaction.atomic
    def deallocate_product(cls, subscription_code, body):
        subscription_obj = SubscriptionService.deallocate_subscription(
            subscription_code,
        )
        res = OcsService.deallocate_subscription(
            subscription_code,
            body,
        )
        if res['data']['deallocation_cause'] == 'normal':
            send_notification_to_mis_with_subscription.delay(
                subscription_code,
                Notification.DeallocationManual().get_email_subject(),
                Notification.DeallocationManual().get_email(
                    subscription_obj.number,
                ),
                Notification.DeallocationManual().get_sms(
                    subscription_obj.number,
                ),
            )

        return True

    @classmethod
    def convert_product(cls, subscription_code, body):
        try:
            subscription_obj = Subscription.objects.get(
                subscription_code=subscription_code,
                is_allocated=True,
            )
        except Subscription.DoesNotExist:
            raise exceptions.NotFound(
                _("Subscription does not exists")
            )
        except Subscription.MultipleObjectsReturned as e:
            raise api_exceptions.Conflict409(detail=e)

        res = OcsService.convert_subscription(
            subscription_code,
            body
        )

        if res["data"]:
            subscription_obj.subscription_type = SUBSCRIPTION_TYPES[0][0]
            subscription_obj.save()

        send_notification_to_mis_with_subscription.delay(
            subscription_code,
            Notification.ConvertPrepaid().get_email_subject(),
            Notification.ConvertPrepaid().get_email(
                subscription_obj.number,
            ),
            Notification.ConvertPrepaid().get_sms(
                subscription_obj.number,
            ),
        )

        return subscription_obj
