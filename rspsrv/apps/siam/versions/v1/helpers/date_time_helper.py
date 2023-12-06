import logging

from django.utils.translation import gettext as _
from jdatetime import datetime

from rspsrv.tools import api_exceptions

logger = logging.getLogger("common")


class DateTimeHelper:
    @classmethod
    def to_object(cls, date_time, to_gregorian=True):
        """
        Test & Convert DateTime from String to DateTime Object.
        :param to_gregorian: Whether result return in gregorian or jalali?
        :param date_time: date-time value in string.
        :return:
        """
        if not date_time:
            return ''

        try:
            date_time = datetime.strptime(
                date_time,
                '%Y/%m/%d %H:%M',
            )
        except ValueError:
            msg = _('DateTime string format is incorrect!')
            logger.error(msg)
            raise api_exceptions.ValidationError400(
                detail=msg,
            )

        return date_time.togregorian() if to_gregorian else date_time
