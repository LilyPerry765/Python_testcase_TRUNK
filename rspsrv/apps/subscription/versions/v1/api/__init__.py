import logging
from datetime import datetime

from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.membership.models import User
from rspsrv.apps.ocs.versions.v1_0.services.ocs import OcsService
from rspsrv.apps.subscription.apps import SubscriptionConfig
from rspsrv.apps.subscription.models import (
    Subscription,
)
from rspsrv.apps.subscription.versions.v1.configs import SubscriptionConfigurations
from rspsrv.apps.subscription.versions.v1.serializers.subscription import (
    SubscriptionAssignSerializer,
    SubscriptionAutoPaySerializer,
    SubscriptionExportSerializer,
    SubscriptionSerializer,
    SubscriptionUpdateSerializer,
)
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.custom_paginator import CustomPaginator
from rspsrv.tools.permissions import (
    Group,
    IsSuperUser,
    IsSupport,
    IsSales,
    IsCustomerAdmin,
    IsCustomerOperator,
    IsFinance,
)
from rspsrv.tools.permissions.base import CheckPermission
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class BaseSubscriptionAPIView(APIView):
    permission_classes = [
        IsSuperUser |
        IsSupport |
        IsSales |
        IsFinance |
        IsCustomerAdmin |
        IsCustomerOperator
    ]


def apply_subscription_filters_and_order(subscriptions, request):
    if "t" in request.query_params:
        query = request.query_params["t"]
        try:
            prime_code = int(
                query,
            )
        except ValueError:
            prime_code = 0
        subscriptions = subscriptions.filter(
            Q(number__icontains=query) |
            Q(destination_number__icontains=query) |
            Q(subscription_code__icontains=query) |
            Q(customer__id__icontains=prime_code)
        )
    else:
        filter_dict = {
            'number': 'number__icontains',
            'destination_number': 'destination_number__icontains',
            'subscription_code': 'subscription_code__icontains',
        }
        filters = Helper.generate_lookup(
            filter_dict,
            request.query_params,
            q_objects=True
        )
        if filters:
            subscriptions = subscriptions.filter(filters)

    if 'subscription_type' in request.query_params:
        subscriptions = subscriptions.filter(
            subscription_type=request.query_params['subscription_type']
        )
    if 'allow_call' in request.query_params:
        try:
            allow_call = int(request.query_params['allow_call'])
        except ValueError:
            allow_call = 3
        if allow_call == 0:
            subscriptions = subscriptions.filter(
                allow_inbound=False,
                allow_outbound=True,
            )
        elif allow_call == 1:
            subscriptions = subscriptions.filter(
                allow_inbound=True,
                allow_outbound=False,
            )
        elif allow_call == 2:
            subscriptions = subscriptions.filter(
                allow_inbound=False,
                allow_outbound=False,
            )
    if 'allow_inbound' in request.query_params:
        subscriptions = subscriptions.filter(
            allow_inbound=Helper.get_bool(
                request.query_params['allow_inbound'],
            )
        )
    if 'allow_outbound' in request.query_params:
        subscriptions = subscriptions.filter(
            allow_outbound=Helper.get_bool(
                request.query_params['allow_outbound'],
            )
        )
    if 'international_call' in request.query_params:
        subscriptions = subscriptions.filter(
            international_call=Helper.get_bool(
                request.query_params['international_call'],
            )
        )
    if 'created_at_from' in request.query_params:
        value = request.query_params['created_at_from']
        try:
            created_at_from = datetime.fromtimestamp(
                float(value)
            )
            subscriptions = subscriptions.filter(
                created_at__gte=created_at_from
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    'created_at_from': _("Date time format is invalid")
                }
            )
    if 'created_at_to' in request.query_params:
        value = request.query_params['created_at_to']
        try:
            created_at_to = datetime.fromtimestamp(
                float(value)
            )
            subscriptions = subscriptions.filter(
                created_at__lte=created_at_to
            )
        except ValueError:
            raise api_exceptions.ValidationError400(
                detail={
                    'created_at_to': _("Date time format is invalid")
                }
            )

    subscriptions = Helper.order_by_query(
        Subscription,
        subscriptions,
        request.query_params,
    )

    return subscriptions


class SubscriptionAPIView(BaseSubscriptionAPIView):
    def get(self, request, subscription_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            sub_args = {
                "is_allocated": True,
                "customer": request.user.customer,
                "id": subscription_id,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            sub_args = {
                "is_allocated": True,
                "operator": request.user,
                "id": subscription_id,
            }
        else:
            sub_args = {
                "is_allocated": True,
                "id": subscription_id,
            }
        try:
            subscription_obj = Subscription.objects.get(**sub_args)
        except Subscription.DoesNotExist:
            raise api_exceptions.NotFound404(
                _("Subscription does not exists")
            )
        force_reload = False
        if 'force_reload' in request.query_params:
            force_reload = True

        cgg_data = OcsService.get_subscription(
            subscription_code=subscription_obj.subscription_code,
            force_reload=force_reload,
        )['data']
        serializer = SubscriptionSerializer(
            subscription_obj,
            context={cgg_data['subscription_code']: cgg_data},
        )

        return response(request, data=serializer.data)

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.UPDATE_SUBSCRIPTION
    )
    def put(self, request, subscription_id):
        if not (CheckPermission.is_support(request) or
                CheckPermission.is_superuser(request)):
            raise api_exceptions.PermissionDenied403()
        update = SubscriptionUpdateSerializer(
            data=Helper.get_dict_from_json(request.body),
        )
        if not update.is_valid():
            raise api_exceptions.ValidationError400(update.errors)
        data = update.data
        res = SubscriptionService.update_subscription(subscription_id, data)
        return response(
            request,
            status=status.HTTP_200_OK,
            data=res,
        )


class SubscriptionsAPIView(BaseSubscriptionAPIView):
    def get(self, request):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            sub_args = {
                "is_allocated": True,
                "customer": request.user.customer,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            sub_args = {
                "is_allocated": True,
                "operator": request.user,
            }
        else:
            sub_args = {
                "is_allocated": True,
            }
        subscriptions = Subscription.objects.filter(
            **sub_args
        )
        force_reload = False
        if 'force_reload' in request.query_params:
            force_reload = True
        subscriptions = apply_subscription_filters_and_order(
            subscriptions,
            request,
        )
        subscriptions, paginator = CustomPaginator().paginate(
            request=request,
            data=subscriptions,
        )
        cgg_data = OcsService.get_subscriptions(
            subscription_codes=[
                g.subscription_code for g in subscriptions
            ],
            bypass_pagination=True,
            force_reload=force_reload,
        )['data']
        serializer = SubscriptionSerializer(
            subscriptions,
            many=True,
            context={item['subscription_code']: item for item in cgg_data},
        )
        subscriptions = serializer.data

        return response(request, data=(subscriptions, paginator))


class SubscriptionsExportAPIView(BaseSubscriptionAPIView):

    def get(self, request, export_type='csv'):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            sub_args = {
                "is_allocated": True,
                "customer": request.user.customer,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            sub_args = {
                "is_allocated": True,
                "operator": request.user,
            }
        else:
            sub_args = {
                "is_allocated": True,
            }
        subscriptions = Subscription.objects.filter(
            **sub_args
        )
        force_reload = False
        if 'force_reload' in request.query_params:
            force_reload = True
        subscriptions = apply_subscription_filters_and_order(
            subscriptions,
            request,
        )
        cgg_data = OcsService.get_subscriptions(
            subscription_codes=[
                g.subscription_code for g in subscriptions
            ],
            bypass_pagination=True,
            force_reload=force_reload,
        )['data']
        serializer = SubscriptionExportSerializer(
            subscriptions,
            many=True,
            context={item['subscription_code']: item for item in cgg_data},
        )

        return Helper.export_csv(request, 'numbers', serializer.data)


class SubscriptionAutoPayAPIView(BaseSubscriptionAPIView):
    permission_classes = [
        IsCustomerAdmin |
        IsCustomerOperator
    ]

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.UPDATE_SUBSCRIPTION_AUTO_PAY
    )
    def post(self, request, subscription_id):
        body = Helper.get_dict_from_json(request.body)
        auto_pay = SubscriptionAutoPaySerializer(
            data=body,
        )
        if not auto_pay.is_valid():
            raise api_exceptions.ValidationError400(
                auto_pay.errors,
            )
        auto_pay = auto_pay.data
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            sub_args = {
                "is_allocated": True,
                "customer": request.user.customer,
                "id": subscription_id,
            }
        else:
            sub_args = {
                "is_allocated": True,
                "operator": request.user,
                "id": subscription_id,
            }
        try:
            subscription_obj = Subscription.objects.get(
                **sub_args
            )
        except Subscription.DoesNotExist:
            return response(
                request,
                error=_("Subscription does not exists"),
                status=404
            )

        OcsService.update_subscription(
            customer_code=request.user.customer.id,
            subscription_code=subscription_obj.subscription_code,
            auto_pay=auto_pay['auto_pay']
        )

        return response(
            request,
            status=status.HTTP_200_OK,
            data=auto_pay['auto_pay'],
        )


class SubscriptionAssignAPIView(BaseSubscriptionAPIView):
    permission_classes = [
        IsCustomerAdmin
    ]

    def get(self, request, subscription_id):
        try:
            subscription_obj = Subscription.objects.get(
                customer=request.user.customer,
                id=subscription_id,
            )
        except Subscription.DoesNotExist:
            return response(
                request,
                error=_("Subscription does not exists"),
                status=404
            )
        assign_to = SubscriptionAssignSerializer(
            data={
                "assign_to": subscription_obj.operator.id if
                subscription_obj.operator else None,
            }
        )

        if not assign_to.is_valid():
            raise api_exceptions.ValidationError400(
                assign_to.errors,
            )

        return response(
            request,
            status=status.HTTP_200_OK,
            data=assign_to.data,
        )

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.ASSIGN_SUBSCRIPTION
    )
    def post(self, request, subscription_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            body = Helper.get_dict_from_json(request.body)
            assign_to = SubscriptionAssignSerializer(
                data=body,
            )
            if not assign_to.is_valid():
                raise api_exceptions.ValidationError400(
                    assign_to.errors,
                )
            assign_to = assign_to.data['assign_to']
            try:
                subscription_obj = Subscription.objects.get(
                    customer=request.user.customer,
                    id=subscription_id
                )
            except Subscription.DoesNotExist:
                return response(
                    request,
                    error=_("Subscription does not exists"),
                    status=404
                )
            try:
                user_obj = User.objects.get(
                    customer=request.user.customer,
                    id=assign_to,
                    groups__name__in=[
                        Group.CUSTOMER_OPERATOR,
                    ]
                )
            except User.DoesNotExist:
                return response(
                    request,
                    error=_("User does not exists"),
                    status=404
                )
            Subscription.objects.filter(
                customer=request.user.customer,
                operator=user_obj,
            ).update(
                operator=None,
            )

            subscription_obj.operator = user_obj
            subscription_obj.save()

            return response(
                request,
                status=status.HTTP_204_NO_CONTENT,
            )
        raise api_exceptions.PermissionDenied403()


class SubscriptionCreditAPIView(BaseSubscriptionAPIView):
    permission_classes = [
        IsSupport
    ]

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.INCREASE_CREDIT_SUBSCRIPTION
    )
    def post(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return response(request, status=status.HTTP_404_NOT_FOUND)

        OcsService.increase_credit_subscription(
            subscription.subscription_code,
            request.body,
        )

        return response(request, data=True)


class SubscriptionBaseBalanceAPIView(BaseSubscriptionAPIView):
    permission_classes = [
        IsSupport
    ]

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.INCREASE_BASE_BALANCE_SUBSCRIPTION
    )
    def post(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return response(request, status=status.HTTP_404_NOT_FOUND)
        try:
            OcsService.increase_base_balance_subscription(
                subscription.subscription_code,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=True)


class SubscriptionDebitAPIView(BaseSubscriptionAPIView):
    permission_classes = [
        IsSuperUser
    ]

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.DEBIT_BALANCE_SUBSCRIPTION
    )
    def post(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return response(
                request,
                status=404
            )
        try:
            OcsService.debit_balance_subscription(
                subscription.subscription_code,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            data=True
        )


class SubscriptionAddBalanceAPIView(BaseSubscriptionAPIView):
    permission_classes = [
        IsSuperUser
    ]

    @log_api_request(
        app_name=SubscriptionConfig.name,
        label=SubscriptionConfigurations.APILabels.ADD_BALANCE_SUBSCRIPTION
    )
    def post(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except Subscription.DoesNotExist:
            return response(request, status=status.HTTP_404_NOT_FOUND)
        try:
            OcsService.add_balance_subscription(
                subscription.subscription_code,
                request.body,
            )
        except api_exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(request, data=True)
