from django.db import transaction
import os

from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import exceptions

from rspsrv.apps.crm.serializers.v3.product_serializers import (
    ProductCreateSerializer,
)
from rspsrv.apps.crm.services.v3.product_service import ProductService
from rspsrv.apps.extension.models import ExtensionStatus
from rspsrv.apps.membership.versions.v1.services.customer import (
    CustomerService,
)
from rspsrv.apps.ocs.versions.v1_0.services.ocs import OcsService
from rspsrv.tools import api_exceptions
from rspsrv.tools.utility import Helper


class TrunkService(ProductService):
    @classmethod
    @transaction.atomic
    def create(cls, params):
        response = {}
        crm_product = ProductCreateSerializer(data=params)
        if not crm_product.is_valid():
            raise api_exceptions.ValidationError400(crm_product.errors)
        crm_product = crm_product.data
        try:
            customer_obj = CustomerService.create_customer(
                crm_product['customer_code'],
            )
        except exceptions.APIException:
            raise

        try:
            subscription_obj = ProductService.create_subscription({
                'package_id': crm_product['package_id'],
                'subscription_code': crm_product['subscription_code'],
                'number': crm_product['number'],
                'base_balance': crm_product['base_balance'],
                'customer_id': customer_obj['id'],
                'max_call_concurrency': crm_product['max_call_concurrency'],
                'destination_number': crm_product['number'],
                'latitude': crm_product['latitude'],
                'longitude': crm_product['longitude'],
                'ip': crm_product['ip'],
                'is_prepaid': crm_product['is_prepaid'],
            })
        except exceptions.APIException:
            raise

        try:
            user_obj = CustomerService.create_or_get_default_user(
                customer_obj['customer_code'],
            )
        except exceptions.APIException:
            OcsService.remove_subscription(
                subscription_code=crm_product['subscription_code'],
            )
            raise

        # Create Extension.
        caller_id = Helper.normalize_number(subscription_obj.number)

        if caller_id is None:
            raise exceptions.ValidationError(
                detail=_('Number "{num}" is not valid!').format(
                    num=subscription_obj.number
                )
            )

        try:
            extension_obj = ProductService.create_extension({
                'has_pro': crm_product['has_pro'],
                'customer': customer_obj['id'],
                'password': Helper.extension_password(),
                'callerid': caller_id,
                'extension_number': subscription_obj.number,
                'web_enabled': False,
                'external_call_enable': True,
                'show_contacts': False,
                'inbox_enabled': False,
                'international_call': False,
                'subscription': subscription_obj.id,
                'status': ExtensionStatus.AVAILABLE.Value,
                'record_all': True,
                'ring_seconds': 40,
                'enabled': True,
                'call_waiting': True,
            })
        except Exception:
            OcsService.remove_subscription(
                subscription_code=crm_product['subscription_code'],
            )
            raise

        response.update({
            'subscription_code': subscription_obj.subscription_code,
            'subscription_type': subscription_obj.subscription_type,
            # change this field of response in version 4
            'gateway': subscription_obj.number,
            'extension': extension_obj.extension_number.number,
            'extension_password': extension_obj.password,
            'sip_domain': os.environ.get("RSPSRV_SBC_DOMAIN"),
            'outbound_proxy': os.environ.get("RSPSRV_SBC_PUBLIC_IP"),
            'user': {
                'prime_code': customer_obj['prime_code'],
                'username': user_obj['username'],
                'password': user_obj['password'],
            },
        })

        #        if not settings.IGNORE_CREATION_FLOW:
        #            try:
        #                DispatcherService.remove_dispatch(
        #                    crm_product['number'],
        #                )
        #            except Exception:
        #                pass
        #            try:
        #                DispatcherService.new_dispatch(
        #                    crm_product['number'],
        #                )
        #            except Exception as e:
        #                OcsService.remove_subscription(
        #                    subscription_code=crm_product['subscription_code'],
        #                )
        #                raise exceptions.APIException(detail=str(e))

        return response
