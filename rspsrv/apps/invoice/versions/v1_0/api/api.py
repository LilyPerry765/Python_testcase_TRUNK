import base64
import json
import logging
from json import JSONDecodeError

from django.shortcuts import render
from django.utils.translation import gettext as _
from rest_framework import exceptions, status
from rest_framework.views import APIView

from rspsrv.apps.api_request.decorators import log_api_request
from rspsrv.apps.file.versions.v1_0.services import FileService
from rspsrv.apps.invoice.apps import InvoiceConfig
from rspsrv.apps.invoice.versions.v1_0.config import InvoiceConfiguration
from rspsrv.apps.invoice.versions.v1_0.services.invoice import (
    InvoiceService
)
from rspsrv.apps.invoice.versions.v1_0.services.pay_with_id_service import PaymentWithID
from rspsrv.apps.membership.versions.v1.services.customer import (
    CustomerService,
)
from rspsrv.apps.mis.versions.v1_0.services.mis import MisService
from rspsrv.apps.subscription.versions.v1.serializers.subscription import (
    SubscriptionCodeSerializer,
)
from rspsrv.apps.subscription.versions.v1.services.subscription import (
    SubscriptionService,
)
from rspsrv.settings.base import STORAGE_BARCODE_PATH
from rspsrv.tools import api_exceptions
from rspsrv.tools.exporter import Exporter
from rspsrv.tools.permissions import (
    Group,
    IsSupport,
    IsCustomerAdmin,
    IsCustomerOperator,
    IsFinance,
    IsSuperUser,
    IsSales,
)
from rspsrv.tools.permissions.base import CheckPermission
from rspsrv.tools.response import http_response
from rspsrv.tools.response import response
from rspsrv.tools.utility import Helper

logger = logging.getLogger("common")


class BaseAdminInvoiceAPIView(APIView):
    permission_classes = [
    #    IsSuperUser |
    #    IsSupport |
    #    IsSales |
    #    IsCustomerAdmin |
    #    IsCustomerOperator |
    #    IsFinance
    ]


def get_subscription_code_from_body(body):
    try:
        body = json.loads(body.decode('utf-8'))
    except JSONDecodeError:
        raise api_exceptions.ValidationError400({
            'non_fields': _('JSON is invalid')
        })
    serializer = SubscriptionCodeSerializer(
        data=body
    )
    subscription_code = None
    if serializer.is_valid(raise_exception=True):
        subscription_code = serializer.data['subscription_code']
    if subscription_code is None:
        raise api_exceptions.ValidationError400({
            'subscription_code': _('field is required')
        })

    return subscription_code


class BaseBalanceInvoiceAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, base_balance_invoice_id=None):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "base_balance_id": base_balance_invoice_id,
            }
        else:
            invoice_args = {
                "base_balance_id": base_balance_invoice_id,
            }

        try:
            cgg_res = InvoiceService.get_base_balance_invoice(**invoice_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_res['data'])


class ExportBaseBalanceInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, export_type):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
                "export_type": export_type,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
                "export_type": export_type,
            }

        try:
            cgg_data = InvoiceService.export_base_balance_invoices(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_data)


class BaseBalanceInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
            }

        try:
            cgg_res = InvoiceService.get_base_balance_invoices(**invoice_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_res,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_res['data'], None),
            **response_kwargs,
        )

    @log_api_request(
        app_name=InvoiceConfig.name,
        label=InvoiceConfiguration.APILabels.CREATE_BASE_BALANCE_INVOICE
    )
    def post(self, request):
        if not CheckPermission.is_customer(request):
            raise api_exceptions.PermissionDenied403(_(
                'Only customers can create new base balance invoices'
            ))
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            subscription_code = get_subscription_code_from_body(
                request.body,
            )
            invoice_args = {
                "customer_code": request.user.customer.id,
                "subscription_code": subscription_code,
                "payload": request.body,
            }
        else:
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "payload": request.body,
            }

        try:
            cgg_res = InvoiceService.create_new_base_balance_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_res['data'])


class CreditInvoiceAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, credit_invoice_id=None):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "credit_id": credit_invoice_id,
            }
        else:
            invoice_args = {
                "credit_id": credit_invoice_id,
            }

        try:
            cgg_credit_invoice = InvoiceService.get_credit_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_credit_invoice['data'])


class CreditInvoiceDownloadAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, credit_invoice_id=None):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "credit_id": credit_invoice_id,
            }
        else:
            invoice_args = {
                "credit_id": credit_invoice_id,
            }

        try:
            cgg_credit_invoice = InvoiceService.get_credit_invoice(
                **invoice_args
            )['data']
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)
        if cgg_credit_invoice['number'] is None:
            cgg_credit_invoice['number'] = ""

        try:
            client = MisService.get_client_info(
                CustomerService.get_subscription_code(
                    cgg_credit_invoice['customer_code']
                ),
            )
        except api_exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        data = {
            'client': client,
            'credit_invoice': cgg_credit_invoice,
            'user': request.user,
        }

        if request.GET.get('html'):
            return render(request, 'credit_invoice.html', data)

        try:
            return Exporter(request).export(
                filename='credit_invoice',
                template='credit_invoice.html',
                data=data,
            )
        except Exception:
            return response(
                request,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=_("Something went wrong")
            )


class ExportCreditInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, export_type):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
                "export_type": export_type,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
                "export_type": export_type,
            }

        try:
            cgg_data = InvoiceService.export_credit_invoices(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_data)


class CreditInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
            }

        try:
            cgg_res = InvoiceService.get_credit_invoices(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_res,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_res['data'], None),
            **response_kwargs,
        )

    @log_api_request(
        app_name=InvoiceConfig.name,
        label=InvoiceConfiguration.APILabels.CREATE_CREDIT_INVOICE
    )
    def post(self, request):
        if not CheckPermission.is_customer(request):
            raise api_exceptions.PermissionDenied403(_(
                'Only customers can create new credit invoices'
            ))
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
                "customer_code": request.user.customer.id,
                "payload": request.body,
            }
        else:
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "payload": request.body,
            }

        try:
            cgg_credit_invoice = InvoiceService.create_credit_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)
        return response(
            request,
            data=cgg_credit_invoice['data'],
        )


class UploadAPIView(BaseAdminInvoiceAPIView):
    @log_api_request(
        app_name=InvoiceConfig.name,
        label=InvoiceConfiguration.APILabels.UPLOAD_INVOICE
    )
    def post(self, request):
        try:
            response_data = FileService.upload_file(
                request,
                mime_types=[
                    'application/pdf',
                    'image/bmp',
                    'image/gif',
                    'image/apng',
                    'image/bmp',
                    'image/jpeg',
                    'image/png',
                    'image/tiff',
                    'image/webp',
                ]
            )
        except exceptions.APIException as e:
            return response(
                request,
                error=e.detail,
                status=e.status_code,
            )

        return response(
            request,
            status=200,
            data=response_data,
            message=_('File uploaded'),
        )


class ExportInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, export_type):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
                "export_type": export_type,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
                "export_type": export_type,
            }

        try:
            cgg_data = InvoiceService.export_invoices(**invoice_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_data)


class InvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
            }

        try:
            cgg_res = InvoiceService.get_invoices(**invoice_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_res,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_res['data'], None),
            **response_kwargs,
        )

    @log_api_request(
        app_name=InvoiceConfig.name,
        label=InvoiceConfiguration.APILabels.CREATE_INTERIM_INVOICE
    )
    def post(self, request):
        if not (CheckPermission.is_customer(
                request) or CheckPermission.is_support(request)):
            raise api_exceptions.PermissionDenied403(
                _("Only customer and support has access to this resource")
            )
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            subscription_code = get_subscription_code_from_body(
                request.body,
            )
            invoice_args = {
                "customer_code": request.user.customer.id,
                "subscription_code": subscription_code,
                "on_demand": True,
            }
        elif request.user.groups.filter(
                name=Group.CUSTOMER_OPERATOR
        ).exists():
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            invoice_args = {
                "customer_code": request.user.customer.id,
                "subscription_code": subscription_obj.subscription_code,
                "on_demand": True,
            }
        else:
            subscription_code = get_subscription_code_from_body(
                request.body,
            )
            invoice_args = {
                "subscription_code": subscription_code,
                "on_demand": False,
            }

        try:
            InvoiceService.create_interim_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, status=status.HTTP_202_ACCEPTED)


class InvoiceAPIView(BaseAdminInvoiceAPIView):

    def get(self, request, invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "invoice_id": invoice_id,
            }
        else:
            invoice_args = {
                "invoice_id": invoice_id,
            }

        try:
            cgg_invoice = InvoiceService.get_invoice(**invoice_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_invoice['data'])


class InvoiceDownloadAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "invoice_id": invoice_id,
            }
        else:
            invoice_args = {
                "invoice_id": invoice_id,
            }

        try:
            invoice = InvoiceService.get_invoice(**invoice_args)['data']
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        # Get Client Info from MIS API.
        try:
            client = MisService.get_client_info(
                invoice['subscription_code'],
            )
        except api_exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        # Convert nanoseconds to minutes for PDF file
        for key in (
                "landlines_local_usage",
                "landlines_long_distance_usage",
                "mobile_usage",
                "landlines_corporate_usage",
                "international_usage",
                "landlines_local_usage_prepaid",
                "landlines_long_distance_usage_prepaid",
                "mobile_usage_prepaid",
                "landlines_corporate_usage_prepaid",
                "international_usage_prepaid",
                "total_usage_prepaid",
                "total_usage_postpaid",
                "total_usage",
        ):
            invoice[key] = Helper.convert_nano_seconds_to_seconds(
                invoice[key],
            )

        prime_code = invoice['prime_code'].split("-")[1]
        payment_id_obj = PaymentWithID(invoice["total_cost_rounded"], prime_code,
                                       invoice["from_date"])
        barcode_obj = {}
        barcode, barcode_name = payment_id_obj.barcode_generator()
        barcode_obj["pay_code"] = payment_id_obj.payment_code_generator()
        barcode_obj["bill_code"] = payment_id_obj.bill_code_generator()
        with open(STORAGE_BARCODE_PATH + barcode_name + ".png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        # TODO: use barcode in template like this with correct size --->
        #  <img width="100" height="50" src="data:image/png;base64,{{ barcode_obj.barcode }}">

        barcode_obj["barcode"] = encoded_string.decode("utf-8")
        invoice['period_cost'] = float(invoice['total_usage_cost_postpaid']) + float(
            invoice['subscription_fee']) + float(invoice[
                                                     'tax_cost']) - float(invoice['discount'])
        data = {
            'client': client,
            'invoice': invoice,
            'user': request.user,
            'barcode_obj': barcode_obj,
            'prime_code': prime_code
        }
        if request.GET.get('html'):
            return render(request, 'invoice.html', data)

        try:
            return Exporter(request).export(
                filename='invoice',
                template='invoice.html',
                data=data,
            )
        except Exception:
            return response(
                request,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error=_("Something went wrong")
            )


class ExportPackageInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, export_type):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
                "export_type": export_type,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
                "export_type": export_type,
            }

        try:
            cgg_data = InvoiceService.export_package_invoices(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return http_response(cgg_data)


class PackageInvoicesAPIView(BaseAdminInvoiceAPIView):
    def get(self, request):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "query_params": request.query_params,
            }
        else:
            invoice_args = {
                "query_params": request.query_params,
            }

        try:
            cgg_res = InvoiceService.get_package_invoices(**invoice_args)
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        response_kwargs = Helper.get_response_kwargs(
            cgg_res,
            self.request.get_host(),
            self.request.path_info,
        )

        return response(
            request,
            data=(cgg_res['data'], None),
            **response_kwargs,
        )

    @log_api_request(
        app_name=InvoiceConfig.name,
        label=InvoiceConfiguration.APILabels.CREATE_PACKAGE_INVOICE
    )
    def post(self, request):
        if not CheckPermission.is_customer(request):
            raise api_exceptions.PermissionDenied403(_(
                'Only customers can create new package invoice'
            ))
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            subscription_code = get_subscription_code_from_body(
                request.body,
            )
            invoice_args = {
                "customer_code": request.user.customer.id,
                "subscription_code": subscription_code,
                "payload": request.body,
            }
        else:
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            invoice_args = {
                "customer_code": request.user.customer.id,
                "subscription_code": subscription_obj.subscription_code,
                "payload": request.body,
            }

        try:
            cgg_credit_invoice = InvoiceService.create_new_package_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)
        return response(request, data=cgg_credit_invoice['data'])


class PackageInvoiceAPIView(BaseAdminInvoiceAPIView):
    def get(self, request, package_invoice_id):
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
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
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "package_invoice_id": package_invoice_id,
            }
        else:
            invoice_args = {
                "package_invoice_id": package_invoice_id,
            }

        try:
            cgg_package_invoice = InvoiceService.get_package_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)

        return response(request, data=cgg_package_invoice['data'])

    @log_api_request(
        app_name=InvoiceConfig.name,
        label=InvoiceConfiguration.APILabels.UPDATE_PACKAGE_INVOICE
    )
    def patch(self, request, package_invoice_id=None):
        if not CheckPermission.is_customer(request):
            raise api_exceptions.PermissionDenied403(_(
                'Only customers can update package invoices'
            ))
        if request.user.groups.filter(
                name=Group.CUSTOMER_ADMIN
        ).exists():
            invoice_args = {
                "customer_code": request.user.customer.id,
                "package_invoice_id": package_invoice_id,
                "payload": request.body,
            }
        else:
            subscription_obj = SubscriptionService.get_from_operator(
                request.user.customer,
                request.user,
            )
            invoice_args = {
                "subscription_code": subscription_obj.subscription_code,
                "package_invoice_id": package_invoice_id,
                "payload": request.body,
            }

        try:
            cgg_package_invoice = InvoiceService.update_package_invoice(
                **invoice_args
            )
        except exceptions.APIException as e:
            return response(request, status=e.status_code, error=e.detail)
        return response(request, data=cgg_package_invoice['data'])
