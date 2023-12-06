import json
import logging
from datetime import datetime

from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import status, exceptions
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.invoice.versions.v1_0.config import InvoiceConfiguration
from rspsrv.apps.invoice.versions.v1_0.services.invoice import InvoiceService
from rspsrv.apps.payment.apps import PaymentConfig
from rspsrv.apps.payment.versions.v1_0.config.config import (
    PaymentConfiguration,
)
from rspsrv.apps.payment.versions.v1_0.serializers.payment import (
    PaymentApprovalSerializer,
    PaymentSerializer,
)
from rspsrv.apps.payment.versions.v1_0.services.payment import PaymentService
from rspsrv.apps.payment.versions.v1_0.services.payment_gateway import (
    PaymentGatewayService
)
from rspsrv.apps.subscription.models import Subscription
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)
from rspsrv.tools import api_exceptions
from rspsrv.tools.permissions import (
    Group,
    IsSupport,
    IsSales,
    IsCustomerAdmin,
    IsCustomerOperator,
    IsFinance,
    IsSuperUser,
)
from rspsrv.tools.permissions.base import CheckPermission
from rspsrv.tools.response import http_response
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper
from rspsrv.apps.payment.versions.v1_0.services.rabbitmq import RabbitMQ, rabbitmq_publish_async

logger = logging.getLogger("common")


class BasePaymentAPIView(APIView):
    permission_classes = [
        IsSuperUser |
        IsSupport |
        IsSales |
        IsCustomerAdmin |
        IsCustomerOperator |
        IsFinance
    ]


class BaseBalanceInvoicePaymentsAPIView(BasePaymentAPIView):
    def get(self, request, base_balance_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "base_balance_id": base_balance_invoice_id,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "base_balance_id": base_balance_invoice_id,
            }
        else:
            pay_args = {
                "base_balance_id": base_balance_invoice_id,
            }

        try:
            cgg_payments = PaymentService.get_base_balance_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_payments,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_payments['data'], None),
            **response_kwargs,
        )


class ExportBaseBalanceInvoicePaymentsAPIView(BasePaymentAPIView):
    def get(self, request, export_type, base_balance_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "base_balance_id": base_balance_invoice_id,
                "export_type": export_type,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "base_balance_id": base_balance_invoice_id,
                "export_type": export_type,
            }
        else:
            pay_args = {
                "base_balance_id": base_balance_invoice_id,
                "export_type": export_type,
            }

        try:
            cgg_payments = PaymentService.export_base_balance_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_payments)


class CreditInvoicePaymentsAPIView(BasePaymentAPIView):
    def get(self, request, credit_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "credit_id": credit_invoice_id,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "credit_id": credit_invoice_id,
            }
        else:
            pay_args = {
                "credit_id": credit_invoice_id,
            }

        try:
            cgg_payments = PaymentService.get_credit_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_payments,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_payments['data'], None),
            **response_kwargs,
        )


class ExportCreditInvoicePaymentsAPIView(BasePaymentAPIView):
    def get(self, request, export_type, credit_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "credit_id": credit_invoice_id,
                "export_type": export_type,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "credit_id": credit_invoice_id,
                "export_type": export_type,
            }
        else:
            pay_args = {
                "credit_id": credit_invoice_id,
                "export_type": export_type,
            }

        try:
            cgg_payments = PaymentService.export_credit_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_payments)


class InvoicePaymentsAPIView(BasePaymentAPIView):

    def get(self, request, invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "invoice_id": invoice_id,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "invoice_id": invoice_id,
            }
        else:
            pay_args = {
                "invoice_id": invoice_id,
            }

        try:
            cgg_payments = PaymentService.get_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_payments,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_payments['data'], None),
            **response_kwargs,
        )


class ExportInvoicePaymentsAPIView(BasePaymentAPIView):

    def get(self, request, export_type, invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "invoice_id": invoice_id,
                "export_type": export_type,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "invoice_id": invoice_id,
                "export_type": export_type,
            }
        else:
            pay_args = {
                "invoice_id": invoice_id,
                "export_type": export_type,
            }

        try:
            cgg_payments = PaymentService.export_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_payments)


class PaymentsAPIView(BasePaymentAPIView):
    def get(self, request):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "query_params": request.query_params,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
            }
        else:
            pay_args = {
                "query_params": request.query_params,
            }

        try:
            cgg_payments = PaymentService.get_payments(**pay_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_payments,
            self.request.get_host(),
            self.request.path_info,
        )
        return response(
            request,
            data=(cgg_payments['data'], None),
            **response_kwargs,
        )

    @log_api_request(
        app_name=PaymentConfig.name,
        label=PaymentConfiguration.APILabels.CREATE_PAYMENT
    )
    def post(self, request):
        if not CheckPermission.is_customer(request):
            raise api_exceptions.PermissionDenied403(
                _('Only customers can pay for invoices'),
            )
        payment_serializer = PaymentSerializer(
            data=json.loads(request.body.decode('utf-8'))
        )
        if not payment_serializer.is_valid():
            return response(
                request,
                status=status.HTTP_400_BAD_REQUEST,
                error=payment_serializer.errors,
            )
        payment_data = payment_serializer.validated_data
        is_hybrid = payment_data['is_hybrid']
        invoice_id = payment_data['invoice_id']
        invoice_type = payment_data['invoice_type']
        files_id = payment_data['files_id']
        payment_gateway = payment_data['payment_gateway']
        customer_id = request.user.customer.id
        if request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists() and not Subscription.objects.filter(
            is_allocated=True,
            operator=request.user,
            customer=request.user.customer,
        ).exists():
            raise api_exceptions.NotFound404(
                _("Subscription does not exists")
            )
        # Check invoice types to handle credit or online payment
        invoice_types = InvoiceConfiguration.InvoiceTypes
        credit_gateway = PaymentConfiguration.Gateway.CREDIT
        offline_gateway = PaymentConfiguration.Gateway.OFFLINE

        if invoice_type == invoice_types.CREDIT_INVOICE:
            credit_invoice = {
                'id': invoice_id,
                'used_for': None,
            }
        else:
            if payment_gateway == credit_gateway:
                try:
                    cgg_res = InvoiceService.create_credit_invoice(
                        customer_code=customer_id,
                        payload={
                            "operation_type":
                                InvoiceConfiguration.OperationTypes.DECREASE,
                            "used_for": invoice_type,
                            "used_for_id": invoice_id,
                        },
                    )
                    return response(
                        request,
                        status=cgg_res['status'],
                        data=cgg_res['data'],
                    )
                except api_exceptions.APIException as e:
                    return response(
                        request,
                        status=e.status_code,
                        error=e.detail,
                    )
            else:
                credit_invoice = InvoiceService.create_credit_invoice(
                    customer_code=customer_id,
                    payload={
                        "operation_type":
                            InvoiceConfiguration.OperationTypes.INCREASE,
                        "is_hybrid": is_hybrid,
                        "used_for": invoice_type,
                        "used_for_id": invoice_id,
                    },
                )['data']

        try:
            payment_cgg = PaymentService.create_new_payment(
                customer_code=customer_id,
                payload={
                    "credit_invoice_id": credit_invoice['id'],
                    "gateway": payment_gateway,
                    "files": files_id,
                    "extra_data": None
                },
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )
        amount = payment_cgg['data']['amount']
        payment_id = payment_cgg['data']['id']
        if payment_gateway == offline_gateway:
            # End it if it's offline
            payment_info = {
                "message": "offline-payment",
                "username": request.user.username,
                "prime_code": None if not request.user.customer else request.user.customer.prime_code,
                "amount": int(float(amount)),
                "date": payment_cgg['data']['created_at']
            }
            rabbitmq_publish_async.delay(payment_info)
            return response(
                request,
                status=payment_cgg['status'],
                data=payment_cgg['data'],
            )
        # Go through MIS online payment
        # Sorry, generic_field and this process is necessary because of
        # the design of MIS payment API
        generic_field = str(
            payment_cgg['data']['number']
        ).replace('+98', '0') if payment_cgg['data']['number'] else \
            payment_cgg['data']['customer_code']
        app_name = InvoiceConfiguration.InvoiceTypes.INVOICE
        if credit_invoice['used_for'] is None or \
                credit_invoice['used_for'] == '':
            app_name = invoice_types.CREDIT_INVOICE
        elif credit_invoice['used_for'] == \
                invoice_types.BASE_BALANCE_INVOICE:
            app_name = invoice_types.BASE_BALANCE_INVOICE
        elif credit_invoice['used_for'] == \
                invoice_types.PACKAGE_INVOICE:
            app_name = invoice_types.PACKAGE_INVOICE
        try:
            payment_gateway_service = PaymentGatewayService(
                gateway=payment_gateway,
                app=app_name,
                user=request.user,
                related_name='invoice',
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )
        try:
            result = payment_gateway_service.send(
                {
                    'amount': int(float(amount)),
                    'description': payment_data['description'],
                    'related_pay': {
                        'payment_id': payment_id,
                    },
                    # This is to the design of MIS payment API!
                    "generic_field": generic_field,
                    'related_name': 'invoice',
                    'invoice_id': invoice_id,
                    'invoice_type': invoice_type,
                }
            )
        except exceptions.APIException as e:
            return response(
                request,
                status=e.status_code,
                error=e.detail,
            )

        return response(request=request,redirect_to=result['redirect_to'])


class ExportPackageInvoicePaymentsAPIView(BasePaymentAPIView):
    def get(self, request, export_type, package_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "package_invoice_id": package_invoice_id,
                "export_type": export_type
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "package_invoice_id": package_invoice_id,
                "export_type": export_type
            }
        else:
            pay_args = {
                "package_invoice_id": package_invoice_id,
                "export_type": export_type
            }

        try:
            cgg_payments = PaymentService.export_package_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_payments)


class PackageInvoicePaymentsAPIView(BasePaymentAPIView):
    def get(self, request, package_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "package_invoice_id": package_invoice_id,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "package_invoice_id": package_invoice_id,
            }
        else:
            pay_args = {
                "package_invoice_id": package_invoice_id,
            }

        try:
            cgg_payments = PaymentService.get_package_invoice_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_payments,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_payments['data'], None),
            **response_kwargs,
        )


class PaymentApprovalAPIView(BasePaymentAPIView):
    permission_classes = (IsFinance,)

    @log_api_request(
        app_name=PaymentConfig.name,
        label=PaymentConfiguration.APILabels.APPROVE_PAYMENT
    )
    def post(self, request, payment_id):
        try:
            body = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return response(
                request,
                status=status.HTTP_400_BAD_REQUEST,
                error="JSON decode error on body",
            )
        approved_serializer = PaymentApprovalSerializer(
            data=body
        )
        if not approved_serializer.is_valid():
            return response(
                request,
                status=status.HTTP_400_BAD_REQUEST,
                error=approved_serializer.error_messages,
            )

        approved = approved_serializer.data['approved']
        status_code = False
        if approved:
            status_code = True

        try:
            cgg_approval = PaymentService.approval_payment(
                payment_id=payment_id,
                status_code=status_code,
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_approval["data"])


class ExportPaymentsAPIView(BasePaymentAPIView):
    def get(
            self,
            request,
            export_type,
            invoice_id=None,
            base_balance_invoice_id=None,
    ):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            if invoice_id or base_balance_invoice_id:
                pay_args = {
                    "customer_code": request.user.customer.id,
                    "invoice_id": invoice_id,
                    "base_balance_invoice_id": base_balance_invoice_id,
                    "query_params": request.query_params,
                    "export_type": export_type,
                }
            else:
                pay_args = {
                    "customer_code": request.user.customer.id,
                    "query_params": request.query_params,
                    "export_type": export_type,
                }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            if invoice_id or base_balance_invoice_id:
                pay_args = {
                    "subscription_code": subscription_obj.subscription_code,
                    "invoice_id": invoice_id,
                    "base_balance_invoice_id": base_balance_invoice_id,
                    "query_params": request.query_params,
                    "export_type": export_type,
                }
            else:
                pay_args = {
                    "subscription_code": subscription_obj.subscription_code,
                    "query_params": request.query_params,
                    "export_type": export_type,
                }
        else:
            if invoice_id or base_balance_invoice_id:
                pay_args = {
                    "invoice_id": invoice_id,
                    "base_balance_invoice_id": base_balance_invoice_id,
                    "query_params": request.query_params,
                    "export_type": export_type,
                }
            else:
                pay_args = {
                    "query_params": request.query_params,
                    "export_type": export_type,
                }

        try:
            cgg_payments = PaymentService.export_payments(
                **pay_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_payments)


class PaymentAPIView(BasePaymentAPIView):
    def get(self, request, payment_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            pay_args = {
                "customer_code": request.user.customer.id,
                "payment_id": payment_id
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            pay_args = {
                "subscription_code": subscription_obj.subscription_code,
                "payment_id": payment_id
            }
        else:
            pay_args = {
                "payment_id": payment_id
            }

        try:
            cgg_payment = PaymentService.get_payment(**pay_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_payment['data'])
