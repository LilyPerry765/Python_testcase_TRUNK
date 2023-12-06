import codecs
import csv
from collections import OrderedDict
from datetime import datetime

from django.http import (
    HttpResponseRedirect, HttpResponse,
    StreamingHttpResponse,
)
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.response import Response


class RichResponse(Response):
    def __init__(
            self,
            request,
            data=None,
            redirect_to=None,
            status=200,
            error=None,
            hint=None,
            message=None,
            pagination=True,
            **kwargs
    ):
        response = OrderedDict()

        if data and request.method == 'GET' and status == 200 and not \
                isinstance(
                    data, dict) and pagination:
            data, paginator = data

            if paginator:
                response.update([
                    ('count', paginator.count),
                    ('next', paginator.get_next_link()),
                    ('previous', paginator.get_previous_link()),
                ])

        # Check Type of 'error'.
        if isinstance(error, Exception):
            error = error.__str__()

        response.update([
            ("status", status),
            ("error", error),
            ("hint", hint),
            ("message", message),
            ("user_id", request.user.id),
            ("time", datetime.now().timestamp()),
            ("data", data),
        ])

        for kw, val in kwargs.items():
            response.update([
                (kw, val),
            ])

        if redirect_to:
            response.update([
                ('redirect_to', redirect_to),
            ])

        super(RichResponse, self).__init__(data=response, status=status)


def response_ok(req, data=None, message=None, **kwargs):
    return RichResponse(req, data=data, message=message, status=200, **kwargs)


def response_http_redirect(redirect_to):
    # Make url safe for HTTP redirect
    if not redirect_to.startswith("http"):
        redirect_to = "http://{}".format(redirect_to)

    return HttpResponseRedirect(
        redirect_to=redirect_to,
    )


def response4xx(req, data=None, status=None, error=None):
    if status is None:
        status = 400
    return RichResponse(req, data=data, status=status, error=error)


def response400(req, data=None, error=None):
    return RichResponse(req, data=data, status=400, error=error)


def response404(req, data=None, error=None):
    return RichResponse(req, data=data, status=404, error=error)


def response403(req, data=None, error=None):
    return RichResponse(req, data=data, status=403, error=error)


def response_removed(req):
    return RichResponse(
        req,
        data=None,
        status=status.HTTP_410_GONE,
        error=_("This resource is no longer available, use the newest version")
    )


def response_deprecated(req):
    return RichResponse(
        req,
        data=None,
        status=status.HTTP_410_GONE,
        error=_(
            "This resource is going to be removed and no longer valid, "
            "use the newest version")
    )


def response500(req, data=None, error=None):
    return RichResponse(req, data=data, status=500, error=error)


def response(
        request,
        status=200,
        data=None,
        error=None,
        hint=None,
        message=None,
        redirect_to=None,
        pagination=True,
        **kwargs
):
    return RichResponse(
        request=request,
        status=status,
        data=data,
        error=error,
        hint=hint,
        message=message,
        redirect_to=redirect_to,
        pagination=pagination,
        **kwargs,
    )


def pure(status=200, data=None, message=None, error=None, **kwargs):
    """
    Fill & Return Base-Schema Response in format of Dictionary.
    :param status:
    :param data:
    :param message:
    :param error:
    :return:
    """
    result = dict()

    result.update([
        ('status', status),
        ('data', data),
        ('message', message),
        ('error', error),
    ])

    if 'redirect_to' in kwargs:
        result.update([
            ('redirect_to', kwargs.pop('redirect_to'))
        ])

        result.pop('error')

    return result


def http_response(data):
    """
    Data must have these keys: content_type, data, content_disposition
    :param data:
    :type data:
    :return:
    :rtype:
    """
    response_data = HttpResponse(
        content=data['data'],
        content_type=data['content_type'],
    )
    response_data['Content-Disposition'] = data["content_disposition"]

    return response_data


class Echo(object):
    """
    Pseudo buffer
    """

    def write(self, value):
        return value


def csv_response(
        data,
        header,
        name,
):
    """
    :param header: if not None we assume the data is list otherwise a dict
    :type header:
    :param name:
    :type name:
    :type data: list of serialized data
    :return:
    :rtype:
    """

    def stream(rows, headers):
        yield Echo().write(codecs.BOM_UTF8)
        writer = csv.writer(Echo())
        yield writer.writerow(headers if headers else rows[0].keys())
        for row in rows:
            yield writer.writerow(row if headers else row.values())

    response_csv = StreamingHttpResponse(
        stream(data, header), content_type='text/csv; charset=utf-8'
    )
    response_csv['Content-Disposition'] = "attachment; filename={}.csv".format(
        name,
    )

    return response_csv
