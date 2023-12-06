from datetime import datetime

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def get_error_response(status_code: int, err):
    """
    This dict must match the one in cgg.core.response
    :param status_code: a HTTP status code (must be integer)
    :param err: error message (string or dict)
    :return:
    """
    return {
        "status": status_code,
        "error": err,
        "hint": None,
        "message": None,
        "user_id": None,
        "time": datetime.now().timestamp(),
        "data": None,
    }


def rspsrv_exception_handler(exc, context):
    """
    Modify and customize exceptions based on their status code
    :param exc:
    :param context:
    :return:
    """
    res = exception_handler(exc, context)
    if res and getattr(res, 'status_code'):
        if not status.is_success(res.status_code):
            if isinstance(exc, Throttled) and exc.wait is not None:
                error = "{}. {}".format(
                    _("request limit exceeded"),
                    _("try again after {} seconds").format(exc.wait),
                )
            elif not hasattr(res, 'error'):
                if hasattr(res, 'data') and res.data and \
                        (hasattr(res.data, 'detail') or 'detail' in res.data):
                    error = res.data['detail']
                elif getattr(res, 'data') and res.data:
                    error = res.data
                else:
                    error = _("Something went wrong in the request")
            else:
                error = res['error']
            res.data = get_error_response(
                res.status_code,
                error,
            )

    return res
