import datetime
import re

import pytz


class GregorianConvert:

    def __init__(
            self,
            date=None,
            year=None,
            month=None,
            day=None,
            timezone='Asia/Tehran',
    ):
        """
        Either use date (string|date|datetime|tuple) or year,month,day together
        :param date:
        :type date:
        :param year:
        :type year:
        :param month:
        :type month:
        :param day:
        :type day:
        :param timezone:
        :type timezone:
        """
        hours = 0
        minutes = 0
        seconds = 0
        if date is not None:
            if type(date) is str:
                m = re.match(r'^(\d{4})\D(\d{1,2})\D(\d{1,2})$', date)
                if m:
                    [year, month, day] = [int(m.group(1)), int(m.group(2)),
                                          int(m.group(3))]
                else:
                    raise Exception("Invalid Input String")
            elif type(date) is datetime.date:
                [year, month, day] = [date.year, date.month, date.day]
            elif type(date) is datetime.datetime:
                date = date.replace(tzinfo=pytz.UTC).astimezone(
                    pytz.timezone(timezone)
                )
                [year, month, day, hours, minutes, seconds] = [
                    date.year,
                    date.month,
                    date.day,
                    date.hour,
                    date.minute,
                    date.second
                ]
            elif type(date) is tuple:
                year, month, day = date
                year = int(year)
                month = int(month)
                day = int(day)
            else:
                raise Exception("Invalid Input Type")
        elif year is not None and month is not None and day is not None:
            year = int(year)
            month = int(month)
            day = int(day)
        else:
            raise Exception("Invalid Input")

        # Check the validity of input date
        try:
            datetime.datetime(year, month, day, hours, minutes, seconds)
        except Exception:
            raise Exception("Invalid Date")

        self.gregorian_year = year
        self.gregorian_month = month
        self.gregorian_day = day

        # Convert date to Jalali
        d_4 = year % 4
        g_a = [0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
        doy_g = g_a[month] + day
        if d_4 == 0 and month > 2:
            doy_g += 1
        d_33 = int(((year - 16) % 132) * .0305)
        a = 286 if (d_33 == 3 or d_33 < (d_4 - 1) or d_4 == 0) else 287
        if (d_33 == 1 or d_33 == 2) and (d_33 == d_4 or d_4 == 1):
            b = 78
        else:
            b = 80 if (d_33 == 3 and d_4 == 0) else 79
        if int((year - 10) / 63) == 30:
            a -= 1
            b += 1
        if doy_g > b:
            jy = year - 621
            doy_j = doy_g - b
        else:
            jy = year - 622
            doy_j = doy_g + a
        if doy_j < 187:
            jm = int((doy_j - 1) / 31)
            jd = doy_j - (31 * jm)
            jm += 1
        else:
            jm = int((doy_j - 187) / 30)
            jd = doy_j - 186 - (jm * 30)
            jm += 7
        self.persian_year = jy
        self.persian_month = jm
        self.persian_day = jd
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def jalali_tuple(self):
        return self.persian_year, self.persian_month, self.persian_day

    def jalali(self, date_format="{}-{}-{}"):
        return date_format.format(
            self.persian_year,
            self.persian_month,
            self.persian_day,
        )

    def jalali_with_time(self, date_format="{}-{}-{} {}:{}:{}"):
        return date_format.format(
            self.persian_year,
            str(self.persian_month).zfill(2),
            str(self.persian_day).zfill(2),
            str(self.hours).zfill(2),
            str(self.minutes).zfill(2),
            str(self.seconds).zfill(2),
        )
