import datetime

import jdatetime
from django import template

from rspsrv.tools.utility import Helper

register = template.Library()


@register.simple_tag(name='jdate')
def jdate(datetime_object, jformat='%Y/%m/%d'):
    timestamp = datetime.datetime.now().timestamp()
    if datetime_object is None:
        return "-"
    if type(datetime_object) == str:
        timestamp = float(datetime_object)
    elif type(datetime_object) in (int, float):
        timestamp = datetime_object
    elif type(datetime_object) == datetime.datetime:
        timestamp = datetime_object.timestamp()
    elif type(datetime_object) == datetime.date:
        timestamp = float(datetime_object.strftime('%s'))

    return Helper.to_jalali_date(
        jdatetime.datetime.fromtimestamp(timestamp),
        date_format=jformat,
    )
