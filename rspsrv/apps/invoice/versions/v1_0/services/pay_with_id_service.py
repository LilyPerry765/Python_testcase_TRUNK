import datetime

import barcode
import jdatetime
from barcode.writer import ImageWriter

from rspsrv.settings.base import STORAGE_BARCODE_PATH
from rspsrv.tools.utility import Helper


class Codes:
    SUBSIDIARY_COMPANY_CODE = '939'
    SERVICE_CODE = '4'


class PaymentWithID:
    def __init__(self, amount, prime_code, date):
        self.amount = amount
        self.prime_code = prime_code
        self.date = self.to_jalali_date(date)

    def get_year_code(self):
        year = self.date.split("/")[0]
        print("year ", year)
        return year[len(year) - 1]

    def get_period_code(self):
        month = self.date.split("/")[1]
        return '{:02d}'.format(int(month))

    @staticmethod
    def fill_to_fixed_length(subject, length):
        return str(subject).zfill(length)

    def get_amount_remove_thousand(self):
        return int(int(self.amount) / 1000)

    @staticmethod
    def checksum(subject):
        checksum = 0
        i = 2
        for x in range(len(subject) - 1, -1, -1):
            if i > 7:
                i = 2
            checksum += int(subject[x]) * i
            i += 1

        checksum %= 11

        if checksum in [0, 1]:
            return "0"
        else:
            return str(11 - checksum)

    def bill_code_generator(self, for_barcode=False):
        code = str(int(self.prime_code)) + Codes.SUBSIDIARY_COMPANY_CODE + Codes.SERVICE_CODE
        checksum = self.checksum(code)
        if for_barcode:
            code = str(
                self.fill_to_fixed_length(self.prime_code, 8)) + Codes.SUBSIDIARY_COMPANY_CODE + Codes.SERVICE_CODE
        return str(code + checksum)

    def payment_code_generator(self, for_barcode=False):
        part1 = str(self.get_amount_remove_thousand()) + self.get_year_code() + self.get_period_code()
        checksum1 = self.checksum(part1)
        code_part1 = part1 + checksum1
        part2 = self.bill_code_generator() + code_part1
        checksum2 = self.checksum(part2)
        if for_barcode:
            code_part1 = self.fill_to_fixed_length(self.get_amount_remove_thousand(), 8) + self.get_year_code() + \
                         self.get_period_code() + checksum1
        return code_part1 + checksum2

    def barcode_generator(self):
        code = self.bill_code_generator(True) + self.payment_code_generator(True)
        name = self.barcode_image_generator(code)
        return code, name

    def barcode_image_generator(self, code):
        c128 = barcode.get_barcode_class('code128')
        c128 = c128(code, writer=ImageWriter())
        name = "%s-%s" % (code, self.prime_code)
        path = "%s%s" % (STORAGE_BARCODE_PATH, name)
        try:
            c128.save(filename=path,
                      # TODO: May need to change this options to the correct size
                      options=[
                          ("module_width", 0.1),
                          ("module_height", 2),
                          ("text_distance", 1),
                          ("font_size", 5),
                      ])
            return name
        except Exception as e:
            raise e

    def to_jalali_date(self, datetime_object, jformat='%Y/%m/%d - %H:%M'):
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
