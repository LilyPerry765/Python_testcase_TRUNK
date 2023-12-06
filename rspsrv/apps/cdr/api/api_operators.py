import logging
from datetime import datetime

from django.conf import settings
from rest_framework.views import APIView

from rspsrv.apps.cdr.services.services import TIO
from rspsrv.tools.permissions.phone_operator import IsPhoneOperatorPermission
from rspsrv.tools.response import response400, response_ok, response500
from rspsrv.tools.utility import Operator, Helper
from django.utils.translation import gettext as _

logger = logging.getLogger("common")

OPERATORS = (
    ("1", Operator.Codes.MCI),
    ("2", Operator.Codes.Irancell),
    ("3", Operator.Codes.RighTel),
    ("4", Operator.Codes.TCT),
)


class BaseAdminCDRAPIView(APIView):
    permission_classes = [IsPhoneOperatorPermission]


class OperatorCDRAPIView(BaseAdminCDRAPIView):
    def get(self, request, operator):
        direction = request.GET.get("direction")
        if direction is None or direction not in ["in", "out"]:
            return response400(request, error=_("Direction wrong"))
        if operator not in [opt[0] for opt in OPERATORS]:
            return response400(request, error=_("Operator wrong"))

        operator_name = [x[1] for x in OPERATORS if x[0] == operator][0]
        start_date = request.GET.get("df", None)
        end_date = request.GET.get("dt", None)
        if start_date is None or end_date is None:
            return response400(request, error=_("Date range not selected"))

        diff = Helper.diff_days_between_two_dates(start_date, end_date)
        if diff > 31:
            return response400(request, error=_("Date range wrong"))

        offset = int(request.GET.get("offset", 0))
        limit = int(request.GET.get("limit", settings.REST_FRAMEWORK.get("PAGE_SIZE")))
        page = int(offset / limit) + 1
        order_by = request.GET.get('order_by', None)
        if order_by is None:
            order_by = '-created_at'

        params = {
            "order_by": order_by,
            "direction": direction,
            "operator_name": operator_name,
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
        }
        try:
            data = TIO.get_cdr(params)
            response_data = data["data"], False
            return response_ok(request, data=response_data, message="",
                               count=data["total"], total_price=data["total_price"])
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)


class OperatorExportCSVCDRAPIView(BaseAdminCDRAPIView):
    def get(self, request, operator):
        direction = request.GET.get("direction")
        if direction is None or direction not in ["in", "out"]:
            return response400(request, error=_("Direction wrong"))
        if operator not in [opt[0] for opt in OPERATORS]:
            return response400(request, error=_("Operator wrong"))

        operator_name = [x[1] for x in OPERATORS if x[0] == operator][0]
        start_date = request.GET.get("df", None)
        end_date = request.GET.get("dt", None)
        if start_date is None or end_date is None:
            return response400(request, error=_("Date range not selected"))

        diff = Helper.diff_days_between_two_dates(start_date, end_date)
        if diff > 31:
            return response400(request, error=_("Date range wrong"))
        order_by = request.GET.get('order_by', None)
        if order_by is None:
            order_by = '-created_at'

        params = {
            "direction": direction,
            "operator_name": operator_name,
            "start_date": start_date,
            "end_date": end_date,
            "order_by": order_by,
        }
        try:
            data = TIO.get_csv(params)
            response_data = data["data"], False
            return response_ok(request, data=response_data, message="")
        except Exception as e:
            logger.error("Exception: %s" % e)
            return response500(request)
