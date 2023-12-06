import logging
from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework_jwt.views import JSONWebTokenAPIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.membership.apps import MembershipConfig
from rspsrv.apps.membership.models import (
    User,
    UserLoginStatus,
    Customer,
)
from rspsrv.apps.membership.versions.v1.configs import MembershipConfiguration
from rspsrv.apps.membership.versions.v1.serializers.custom_jwt import (
    CustomJSONWebTokenSerializer,
)
from rspsrv.apps.membership.versions.v1.serializers.customer import (
    CustomerMergedSerializer,
)
from rspsrv.apps.membership.versions.v1.serializers.user import (
    UserSerializer,
)
from rspsrv.apps.membership.versions.v1.services.user import UserService
from rspsrv.apps.ocs.versions.v1_0.services.ocs import OcsService
from rspsrv.tools import api_exceptions
from rspsrv.tools.custom_paginator import CustomPaginator
from rspsrv.tools.jwt_payload_handler import jwt_payload_handler
from rspsrv.tools.permissions import (
    Group as PermissionGroup,
    IsSupport,
    IsCustomerAdmin,
    IsFinance,
    IsCustomerOperator,
    IsSuperUser,
    IsSales,
)
from rspsrv.tools.permissions.base import CheckPermission
from rspsrv.tools.permissions.phone_operator import IsPhoneOperatorPermission
from rspsrv.tools.response import response
from rspsrv.tools.throttle_handler import (
    AnonDayRateThrottle,
    AnonHourRateThrottle,
    AnonMinRateThrottle,
)
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


def get_update_user_groups(user):
    """
    Access to groups for update user from request.user
    :param user:
    :return:
    """
    if user.is_superuser:
        groups = [
            PermissionGroup.FINANCE,
            PermissionGroup.SALES,
            PermissionGroup.CUSTOMER_ADMIN,
            PermissionGroup.CUSTOMER_OPERATOR,
            PermissionGroup.SUPPORT_ADMIN,
            PermissionGroup.SUPPORT_OPERATOR,
            PermissionGroup.PHONE_OPERATOR,
        ]
    elif user.groups.filter(
            name=PermissionGroup.SUPPORT_ADMIN,
    ).exists():
        groups = [
            PermissionGroup.FINANCE,
            PermissionGroup.SALES,
            PermissionGroup.CUSTOMER_ADMIN,
            PermissionGroup.CUSTOMER_OPERATOR,
            PermissionGroup.SUPPORT_OPERATOR,
        ]
    elif user.groups.filter(
            name=PermissionGroup.SUPPORT_OPERATOR,
    ).exists():
        groups = [
            PermissionGroup.CUSTOMER_ADMIN,
            PermissionGroup.CUSTOMER_OPERATOR,
            PermissionGroup.FINANCE,
            PermissionGroup.SALES,
        ]
    elif user.groups.filter(
            name=PermissionGroup.CUSTOMER_ADMIN
    ).exists():
        groups = [
            PermissionGroup.CUSTOMER_OPERATOR,
        ]
    elif user.groups.filter(
            Q(name=PermissionGroup.CUSTOMER_OPERATOR) |
            Q(name=PermissionGroup.SALES) |
            Q(name=PermissionGroup.FINANCE)
    ).exists():
        groups = []
    else:
        raise api_exceptions.PermissionDenied403()

    return groups


def set_user_status(user):
    try:
        guid = user.guid
        rsp_id = settings.WEBSITE_DOMAIN

        payload = {
            'guid': guid,
            'user_status': UserLoginStatus.ONLINE,
            'rsp_id': rsp_id,
        }

        res = requests.post(
            settings.MEMBERSHIP_EXPORT_USERSTAT_URI,
            data=payload,
        )

        if res.status_code != status.HTTP_200_OK:
            return None
        else:
            res = res.json()

            if res['status_code'] != 200:
                return None

        data = {
            'guid': guid,
            'rsp_id': rsp_id,
        }

        return data

    except Exception as e:
        logger.error("Exception: %s" % e)
        return None


class BaseMembershipAPIView(APIView):
    permission_classes = [
        IsSupport |
        IsFinance |
        IsSales |
        IsCustomerAdmin |
        IsCustomerOperator |
        IsSuperUser |
        IsPhoneOperatorPermission
    ]


class CustomObtainJSONWebToken(JSONWebTokenAPIView):
    serializer_class = CustomJSONWebTokenSerializer


class CustomerAPIView(BaseMembershipAPIView):
    def get(self, request, customer_id):
        if CheckPermission.is_customer(request):
            customer_id = request.user.customer.id
        try:
            customer = Customer.objects.get(
                id=customer_id,
            )
        except Customer.DoesNotExist:
            raise api_exceptions.NotFound404(_("Customer does not exists"))
        cgg_data = OcsService.get_customer(
            customer_code=customer.id,
        )['data']
        customer_serializer = CustomerMergedSerializer(
            customer,
            context={cgg_data['customer_code']: cgg_data},
        )

        return response(request, data=customer_serializer.data)


class CustomersAPIView(BaseMembershipAPIView):
    def get(self, request):
        customers = Customer.objects.all()
        if CheckPermission.is_customer(request):
            customers = customers.filter(
                id=request.user.customer.id,
            )
        if "t" in request.query_params:
            query = request.query_params["t"]
            try:
                prime_code = int(
                    query,
                )
            except ValueError:
                prime_code = 0
            customers = customers.filter(
                Q(customer__id__icontains=prime_code)
            )
        if 'created_at_from' in request.query_params:
            value = request.query_params['created_at_from']
            try:
                created_at_from = datetime.fromtimestamp(
                    float(value)
                )
                customers = customers.filter(
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
                customers = customers.filter(
                    created_at__lte=created_at_to
                )
            except ValueError:
                raise api_exceptions.ValidationError400(
                    detail={
                        'created_at_to': _("Date time format is invalid")
                    }
                )

        customers = Helper.order_by_query(
            Customer,
            customers,
            request.query_params,
        )
        customers, paginator = CustomPaginator().paginate(
            request=request,
            data=customers,
        )
        cgg_data = OcsService.get_customers(
            customer_codes=[
                str(c.id) for c in customers
            ],
            bypass_pagination=True,
        )['data']

        customers = CustomerMergedSerializer(
            customers,
            many=True,
            context={item['customer_code']: item for item in cgg_data},
        )

        return response(request, data=(customers.data, paginator))


class UserLoginAPIView(CustomObtainJSONWebToken):
    throttle_classes = [
        AnonMinRateThrottle,
        AnonHourRateThrottle,
        AnonDayRateThrottle,
    ]

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.LOGIN
    )
    def post(self, request, **kwargs):
        body = Helper.get_dict_from_json(request.body)
        try:
            login_data = UserService.login_user(body)
        except exceptions.APIException as e:
            return response(
                request,
                error=e.detail,
                status=e.status_code,
            )

        super_response = super().post(
            request,
            **login_data,
        )
        if super_response.status_code == requests.codes.ok:
            data = {'token': super_response.data['token']}

            return response(request, data=data)
        else:
            raise api_exceptions.AuthenticationFailed401()


class UserGenerateTokenAPIView(APIView):
    throttle_classes = [
        AnonMinRateThrottle,
        AnonHourRateThrottle,
        AnonDayRateThrottle,
    ]
    permission_classes = [

    ]

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.GENERATE_TOKEN
    )
    def post(self, request, **kwargs):
        body = Helper.get_dict_from_json(request.body)
        try:
            mobile = UserService.generate_token(body)
        except exceptions.APIException as e:
            return response(
                request,
                error=e.detail,
                status=e.status_code,
            )

        return response(
            request,
            status=status.HTTP_202_ACCEPTED,
            data={
                "mobile": mobile,
            }
        )


class UsersAPIView(BaseMembershipAPIView):
    def get(self, request):
        users = User.objects.all()
        if CheckPermission.is_customer(request):
            users = users.filter(
                customer=request.user.customer,
            )

        if "t" in request.query_params:
            query = request.query_params["t"]
            try:
                prime_code = int(
                    query,
                )
            except ValueError:
                prime_code = 0
            users = users.filter(
                Q(mobile__icontains=query) |
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(customer__id__icontains=prime_code)
            )
        if "group" in request.query_params:
            groups = [
                x.strip() for x in request.query_params['group'].split(',')
            ]
            users = users.filter(groups__name__in=groups).distinct()
        if "group_type" in request.query_params:
            groups = [
                PermissionGroup.CUSTOMER_ADMIN,
                PermissionGroup.CUSTOMER_OPERATOR,
            ]
            if str(request.query_params["group_type"]) == "1":
                groups = [
                    PermissionGroup.FINANCE,
                    PermissionGroup.SALES,
                    PermissionGroup.SUPPORT_OPERATOR,
                    PermissionGroup.SUPPORT_ADMIN,
                ]
            users = users.filter(groups__name__in=groups).distinct()
        users = Helper.order_by_query(
            User,
            users,
            request.query_params,
        )
        users, paginator = CustomPaginator().paginate(
            request=request,
            data=users,
        )
        users = UserSerializer(
            users,
            many=True,
        )

        return response(request, data=(users.data, paginator))

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.CREATE_USER
    )
    def post(self, request):
        body = Helper.get_dict_from_json(request.body)
        if request.user.is_superuser:
            if 'group' not in body:
                raise api_exceptions.ValidationError400({
                    'group': _("Select a group for new user")
                })
            elif body['group'] not in (
                    PermissionGroup.SUPPORT_ADMIN,
                    PermissionGroup.SUPPORT_OPERATOR,
                    PermissionGroup.FINANCE,
                    PermissionGroup.SALES,
                    PermissionGroup.PHONE_OPERATOR,
            ):
                raise api_exceptions.ValidationError400({
                    'group': _("Select a valid group for new user")
                })
        elif request.user.groups.filter(
                Q(name=PermissionGroup.SUPPORT_ADMIN),
        ).exists():
            if 'group' not in body:
                body['group'] = PermissionGroup.SUPPORT_OPERATOR
            elif body['group'] not in (
                    PermissionGroup.SUPPORT_OPERATOR,
                    PermissionGroup.FINANCE,
                    PermissionGroup.SALES,
            ):
                raise api_exceptions.ValidationError400({
                    'group': _("Select a valid group for new user")
                })
        elif request.user.groups.filter(
                Q(name=PermissionGroup.SUPPORT_OPERATOR),
        ).exists():
            if 'group' not in body:
                raise api_exceptions.ValidationError400({
                    'group': _("Select a group for new user")
                })
            elif body['group'] not in (
                    PermissionGroup.FINANCE,
                    PermissionGroup.SALES,
            ):
                raise api_exceptions.ValidationError400({
                    'group': _("Select a valid group for new user")
                })
        elif request.user.groups.filter(
                Q(name=PermissionGroup.CUSTOMER_ADMIN),
        ).exists():
            body['customer_code'] = request.user.customer.customer_code
            body['group'] = PermissionGroup.CUSTOMER_OPERATOR
        else:
            raise api_exceptions.PermissionDenied403()

        try:
            data = UserService.create_user(body)
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail
            )
        return response(
            request,
            data=data,
        )


class UserAPIView(BaseMembershipAPIView):
    def get(self, request, user_id):
        if CheckPermission.is_customer(request):
            try:
                user = User.objects.get(
                    id=user_id,
                    customer=request.user.customer
                )
            except User.DoesNotExist:
                raise api_exceptions.NotFound404(_("User does not exists"))
        else:
            try:
                user = User.objects.get(
                    id=user_id,
                )
            except User.DoesNotExist:
                raise api_exceptions.NotFound404(_("User does not exists"))

        user_serializer = UserSerializer(
            user,
        )

        return response(request, data=user_serializer.data)

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.UPDATE_USER
    )
    def patch(self, request, user_id):
        body = Helper.get_dict_from_json(request.body)
        groups = get_update_user_groups(request.user)
        if len(groups) == 0 and request.user.id != user_id:
            raise api_exceptions.PermissionDenied403(_(
                "You don't have permission to update other users"
            ))
        try:
            user_data = UserService.update_user(
                groups,
                body,
                user_id,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_200_OK,
            data=user_data,
        )

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.DELETE_USER
    )
    def delete(self, request, user_id):
        groups = get_update_user_groups(request.user)
        if len(groups) == 0:
            raise api_exceptions.PermissionDenied403(_(
                "You don't have permission to delete users"
            ))
        try:
            UserService.delete_user(
                groups,
                user_id,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class UserRenewPasswordAPIView(BaseMembershipAPIView):
    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.RESET_PASSWORD
    )
    def patch(self, request, user_id):
        if str(request.user.id) != str(user_id):
            raise api_exceptions.PermissionDenied403(
                _("Can not reset password for other users")
            )
        body = Helper.get_dict_from_json(
            request.body,
        )
        try:
            UserService.renew_password(
                user_id,
                body,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        update_session_auth_hash(request, request.user)

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class UserSetPasswordAPIView(BaseMembershipAPIView):
    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.SET_PASSWORD
    )
    def patch(self, request, user_id):
        body = Helper.get_dict_from_json(request.body)
        groups = get_update_user_groups(request.user)
        try:
            UserService.force_set_password(
                body,
                groups,
                user_id,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_200_OK,
        )


class UserEmpowerAPIView(BaseMembershipAPIView):
    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.EMPOWER_USER
    )
    def patch(self, request, user_id):
        body = Helper.get_dict_from_json(request.body)
        groups = get_update_user_groups(request.user)
        if len(groups) == 0:
            raise api_exceptions.PermissionDenied403(_(
                "You don't have permission to empower users"
            ))
        try:
            UserService.empower_user(
                body,
                groups,
                user_id,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_200_OK,
        )


class RecoverPasswordAPIView(APIView):
    permission_classes = []

    def get(self, request):
        prime_code = request.GET.get('prime_code', None)
        key = request.GET.get('key', None)
        try:
            UserService.recover_password(
                prime_code,
                key,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class RecoverPasswordConfirmAPIView(APIView):
    permission_classes = []

    def get(self, request):
        token = request.GET.get('token', None)
        if not token:
            raise api_exceptions.ValidationError400(
                {
                    'token': _("This field is required")
                }
            )
        try:
            UserService.recover_password_confirm(
                token,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class RecoverPasswordResetAPIView(APIView):
    permission_classes = []

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.RECOVER_PASSWORD_RESET
    )
    def post(self, request):
        body = Helper.get_dict_from_json(request.body)
        try:
            UserService.recover_password_reset(
                body,
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(
            request,
            status=status.HTTP_204_NO_CONTENT,
        )


class ImpersonateAPIView(APIView):
    permission_classes = [IsSupport]

    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.IMPERSONATE_USER
    )
    def post(self, request):
        current_token = request.META.get('HTTP_AUTHORIZATION')
        try:
            user = User.objects.get(id=request.data['user'])
        except User.DoesNotExist:
            return response(
                request,
                status=400,
                error=_("User does not exists!")
            )

        new_token = jwt_payload_handler(
            current_token,
            user,
            request,
            impersonate=True
        )

        return response(request, data={'token': new_token['token']})


class RevokeImpersonateAPIView(APIView):
    @log_api_request(
        app_name=MembershipConfig.name,
        label=MembershipConfiguration.APILabels.REVOKE_IMPERSONATE_USER
    )
    def post(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        try:
            user = User.objects.get(
                id=Helper.jwt_decode(token.replace('JWT ', ''))['orig_user']
            )
        except User.DoesNotExist:
            return response(
                request,
                status=400,
                error=_("User does not exists!")
            )

        new_token = jwt_payload_handler(token, user)

        return response(request, data={'token': new_token['token']})
