import calendar
import json
import logging
import os
import random
import re
import string
import subprocess
import uuid
from datetime import datetime
from json import JSONDecodeError
from subprocess import check_output

import jdatetime
import jwt
import magic
import math
import pytz
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _
from pydub import AudioSegment
from rest_framework import status

from rspsrv.tools import api_exceptions
from rspsrv.tools.response import response, csv_response

logger = logging.getLogger(__name__)


class BaseChoice(object):
    def __init__(self, label, value):
        self.Label = label
        self.Value = value

    def __repr__(self):
        return self.Value

    def __eq__(self, other):
        # God bless python... there would be no exception.
        return self.Value == other


class Helper(object):
    @classmethod
    def normalize_number(cls, number):
        """
        Normalize number based on E.164 format
        :param number:
        :return: Normalized number
        """
        if number and re.match(re.compile(r'^\+?\d+(?:,\d*)?$'), number):
            if number.startswith("+"):
                return number
            elif number.startswith("00"):
                return "+{}".format(number[2:])
            elif number.startswith("0"):
                return "+98{}".format(number[1:])
            elif number.startswith("98"):
                return "+{}".format(number)
            else:
                return "+98{}".format(number)

    @classmethod
    def set_id_from_number(cls, number):
        """
        Return a `set_id` friendly number for Kamailio
        :param number:
        :return: Normalized number
        @FIXME: This may leads to problems in branches (prefix is removed)
        """
        if len(number) > 8:
            return number[-8:]
        return number

    @staticmethod
    def convert_nano_seconds_to_minutes(nanoseconds):
        nanoseconds = float(nanoseconds)
        if nanoseconds == 0:
            return nanoseconds

        minutes = float(float(nanoseconds / 1000000000) / 60)

        return str(round(minutes, 2))

    @staticmethod
    def convert_nano_seconds_to_seconds(nanoseconds):
        nanoseconds = float(nanoseconds)
        if nanoseconds == 0:
            return nanoseconds

        seconds = float(nanoseconds / 1000000000)

        return str(math.ceil(seconds))

    @staticmethod
    def get_timestamp(date):

        if date is None:
            return None

        timestamp = int(calendar.timegm(date.utctimetuple()))

        return timestamp

    @staticmethod
    def get_jalai_from_timestamp(timestamp):
        return jdatetime.datetime.fromtimestamp(timestamp)

    @staticmethod
    def is_password_weak(value):
        return not bool(
            re.match(
                "^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!#$%&@])(?=.{12,})",
                value,
            )
        )

    @staticmethod
    def is_password_weak_extension(value):
        return not bool(
            re.match(
                "^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@$%^&*])(?=.{8,})",
                value,
            )
        )

    @staticmethod
    def extension_password(length=8):
        upper = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        lower = list("abcdefghijklmnopqrstuvwxyz")
        number = list("0123456789")
        symbol = list("!@$%^&*()")
        index = int(length / 4)
        mod = int(length % 4)
        random_password = random.choices(upper, k=index + mod) + \
                          random.choices(lower, k=index) + \
                          random.choices(number, k=index) + \
                          random.choices(symbol, k=index)

        random.shuffle(random_password)
        random_password = ''.join(random_password)
        return random_password

    @staticmethod
    def generate_strong_password(length=12):
        upper = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        lower = list("abcdefghijklmnopqrstuvwxyz")
        number = list("0123456789")
        symbol = list("$,:;=?@'<>.^*()%!-")
        index = int(length / 4)
        mod = int(length % 4)
        random_password = random.choices(upper, k=index + mod) + \
                          random.choices(lower, k=index) + \
                          random.choices(number, k=index) + \
                          random.choices(symbol, k=index)
        random.shuffle(random_password)
        random_password = ''.join(random_password)
        return random_password

    @staticmethod
    def get_random_string(length=20, case=None, use_number=True):
        if not case:
            letters = string.ascii_letters
        elif case.lower() == 'u':
            letters = string.ascii_uppercase
        elif case.lower() == 'l':
            letters = string.ascii_lowercase
        else:
            letters = string.ascii_letters

        if use_number:
            letters += string.digits

        return ''.join(random.choice(letters) for _ in range(length))

    @staticmethod
    def is_mobile_number(number):
        if number is None or number == '':
            return False

        pattern = re.compile(r'^(\+?98|0?)9[0-9]\d{8}$')
        if not pattern.match(number):
            return False

        return True

    @staticmethod
    def is_valid_number(number):
        if number is None or number == '':
            return False

        pattern = re.compile(r'^\+?\d+(?:,\d*)?$')
        if not pattern.match(number):
            return False

        return True

    @classmethod
    def to_jalali_date(
            cls,
            gregorian_date,
            date_format="%Y/%m/%d %H:%M:%S",
            timezone='Asia/Tehran',
    ):
        if gregorian_date:
            return jdatetime.datetime.fromtimestamp(
                gregorian_date.timestamp(),
            ).replace(tzinfo=pytz.UTC).astimezone(
                pytz.timezone(timezone)
            ).strftime(
                date_format,
            )
        return " - "

    @classmethod
    def to_string_for_export(cls, value, is_boolean=False):
        if value is not None:
            if is_boolean:
                if value:
                    return _("Yes")
                return _("No")
            return str(value)
        return " - "

    @staticmethod
    def generate_guid():
        return str(uuid.uuid4()).replace('-', '')

    @staticmethod
    def jwt_encode(payload, key=settings.SECRET_KEY, algorithm='HS256',
                   encoding='ASCII'):
        return str(jwt.encode(payload=payload, key=key, algorithm=algorithm),
                   encoding=encoding)

    @staticmethod
    def jwt_decode(token, key=settings.SECRET_KEY, algorithms=None):
        if algorithms is None:
            algorithms = ['HS256']

        return jwt.decode(token, key=key, algorithms=algorithms)

    @staticmethod
    def remove_file(path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    @staticmethod
    def remove_empty_directory(path):
        try:
            os.rmdir(path)
        except FileNotFoundError:
            pass

    @staticmethod
    def get_pid_by_name(name):
        pid = None

        try:
            pid = check_output(["pidof", name]).decode('utf-8')

        except Exception as e:
            logger.error("Exception: %s" % e)

        return pid

    @staticmethod
    def convert_pdf2tiff(input_pdf, output_tiff=None, device='tiffg4',
                         paper_size='letter'):

        if output_tiff is None:
            output_tiff = '.'.join([Helper.get_random_string(), 'tiff'])

        base_dir = os.path.dirname(output_tiff)

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        base_command = "gs -q -dNOPAUSE -dBATCH -sDEVICE={device} " \
                       "-sPAPERSIZE={paper_size} -sOutputFile={output_tiff} " \
                       "{input_pdf}"

        convert_command = base_command.format(device=device,
                                              paper_size=paper_size,
                                              input_pdf=input_pdf,
                                              output_tiff=output_tiff)

        subprocess.call(convert_command, shell=True)

        return os.path.abspath(output_tiff)

    @staticmethod
    def convert_tiff2pdf(input_tiff, output_pdf=None, density='300x300',
                         compress='jpeg'):

        if output_pdf is None:
            output_pdf = '.'.join([Helper.get_random_string(), 'pdf'])

        base_dir = os.path.dirname(output_pdf)

        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        base_command = "convert {input_tiff} -density {density} -compress {" \
                       "compress} {output_pdf}"

        convert_command = base_command.format(input_tiff=input_tiff,
                                              output_pdf=output_pdf,
                                              density=density,
                                              compress=compress)

        subprocess.call(convert_command, shell=True)

        return os.path.abspath(output_pdf)

    @staticmethod
    def convert_mp3_to_wav(input_mp3, output_wav=None, rate=8000):
        if output_wav is None:
            output_wav = '.'.join([Helper.get_random_string(), 'wav'])

        base_dir = os.path.dirname(output_wav)

        if not os.path.exists(base_dir) and base_dir:
            os.makedirs(base_dir)

        base_command = "sox -t mp3 {input_mp3} -c 1 -t wav {output_wav} rate" \
                       " {rate}"

        convert_command = base_command.format(input_mp3=input_mp3,
                                              output_wav=output_wav, rate=rate)
        subprocess.call(convert_command, shell=True)

        sound = AudioSegment.from_wav(output_wav)
        sound = sound.set_channels(1)
        sound.export(output_wav, format="wav")

        return os.path.abspath(output_wav)

    @staticmethod
    def is_fax_valid_file(file):
        if Helper.is_pdf_file(file) or Helper.is_tiff_file(file):
            return True

        return False

    @staticmethod
    def is_tiff_file(file):
        mime = magic.Magic(mime=True)
        mime = mime.from_file(file)

        if mime == 'image/tiff':
            return True

        return False

    @staticmethod
    def is_pdf_file(file):
        mime = magic.Magic(mime=True)
        mime = mime.from_file(file)

        if mime == 'application/pdf':
            return True

        return False

    @staticmethod
    def is_mp3_file(file):
        if file is None:
            return False

        mime = magic.Magic(mime=True)
        mime = mime.from_file(file)

        if mime in settings.APPS['general_resource']['mp3_mime_types']:
            return True

        return False

    @staticmethod
    def diff_days_between_two_dates(start_date, end_date):
        d1 = datetime.strptime(start_date, "%Y-%m-%d")
        d2 = datetime.strptime(end_date, "%Y-%m-%d")
        return abs((d2 - d1).days)

    @staticmethod
    def export_csv(
            request,
            name,
            data,
            header=None,
    ):
        """
        Export data to csv format with proper naming
        :param header: if not None we assume the data is list otherwise a dict
        :type header:
        :param request:
        :type request:
        :param name:
        :type name:
        :param data:
        :type data:
        :return:
        :rtype:
        """
        if len(data) == 0:
            return response(
                request,
                error=_("No data for export"),
                status=status.HTTP_404_NOT_FOUND,
            )
        file_name = "{} - {}".format(
            name,
            str(datetime.now().timestamp())
        )

        return csv_response(data, header, file_name)

    @staticmethod
    def get_wav_duration(wav_file):
        duration = subprocess.check_output(['soxi', '-D', wav_file])

        return int(float(duration.decode('utf-8').strip()))

    @staticmethod
    def get_response_kwargs(data, base_url, uri):
        kwargs = dict()
        if 'next' not in data:
            return {}
        if data['next'] is not None:
            kwargs['next'] = base_url + uri + \
                             data['next'].partition('?')[2]
        else:
            kwargs['next'] = None

        if data['previous'] is not None:
            kwargs['previous'] = base_url + uri + \
                                 data['previous'].partition('?')[2]
        else:
            kwargs['previous'] = None

        kwargs['count'] = data['count']

        return kwargs

    @staticmethod
    def generate_lookup(filters, params, q_objects=False, operand='OR'):
        """
        Generate The Dictionary/Q-Objects according to Filters Criteria &
        Params which It's Compatible with Django
        Models Filtering.
        e.g:
        filters_criteria = {'username': 'username__icontains'}
        params = {'username': 'admin'}

        :param operand:
        :param q_objects:
        :param filters:
        :param params:
        :return:
        """
        if len(params) == 0:
            return None

        lookup = {}

        if 't' in params:
            # Set 'term' Value for all Fields.
            for filter_key in filters:
                lookup.update({filters[filter_key]: params['t']})
        else:
            for filter_key in filters:
                filter_value = params.get(filter_key)
                if filter_value is not None:
                    if isinstance(filter_value,
                                  str) and filter_value.strip() == '':
                        continue
                    lookup.update({filters[filter_key]: params[filter_key]})

        if q_objects:
            # Return List of Q Objects in OR Condition.
            qs = None

            for key, lookup_item in lookup.items():
                if qs:
                    qs = qs | Q(
                        **{key: lookup_item}) if operand == 'OR' else qs & Q(
                        **{key: lookup_item})
                else:
                    qs = Q(**{key: lookup_item})

            return qs

        return lookup

    @staticmethod
    def get_dict_from_json(json_string):
        """
        Convert json string to dict (API Exception handled)
        :param json_string:
        :return: dict
        """
        try:
            if isinstance(json_string, bytes):
                json_string = json_string.decode('utf-8')
            json_dict = json.loads(json_string)
        except (JSONDecodeError, ValueError):
            raise api_exceptions.ValidationError400({
                'non_fields': _('JSON is not valid')
            })

        return json_dict

    @staticmethod
    def is_email(email):
        return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))

    @staticmethod
    def get_bool(value=None):
        if not value:
            return False

        try:
            value = int(value)
        except ValueError:
            value = value.strip()
            return value.lower() == 'true'
        else:
            return value > 0

    @staticmethod
    def translator(key):
        """
        Translate keys to the target language
        :param key:
        :return:
        """
        if key == "prepaid":
            return _("Prepaid")
        elif key == "postpaid":
            return _("Postpaid")
        elif key == "base_balance_invoice":
            return _("Base balance invoice")
        elif key == "credit_invoice":
            return _("Credit invoice")
        elif key == "invoice":
            return _("Invoice")
        elif key == "package_invoice":
            return _("Package invoice")
        elif key == "decrease":
            return _("Decrease")
        elif key == "increase":
            return _("Increase")

        return key

    @classmethod
    def order_by_query(cls, class_object, query_object, query_params):
        if 'order_by' in query_params:
            order_field_error = []
            order_by = [
                x.strip() for x in query_params['order_by'].split(',')
            ]
            for order in order_by:
                if not class_object.model_field_exists(
                        order.replace('-', ''),
                ):
                    order_field_error.append(order)
            if order_field_error:
                raise api_exceptions.ValidationError400(
                    {
                        'non_fields': _("Field does not exists"),
                        'errors': order_field_error,
                    }
                )

            query_object = query_object.order_by(
                *order_by
            )

        return query_object

    @staticmethod
    def time_difference_in_minutes(
            to_hour=8,
            to_minute=30,
            time_zone="Asia/Tehran",
    ):
        """
        Return the time difference from now to to_time in UTC
        :param to_hour: 0 <= x < 24
        :type to_hour: int
        :param to_minute: 0 <= x < 60
        :type to_minute: int
        :param time_zone:
        :type time_zone: str
        :return:
        :rtype:
        """
        assert 0 <= to_hour < 23
        assert 0 <= to_minute < 60
        now = datetime.now(tz=pytz.timezone(time_zone))
        to_day = now.day
        if to_hour < now.hour or (
                to_hour == now.hour and to_minute < now.minute
        ):
            to_day += 1
        to = datetime(
            year=now.year,
            month=now.month,
            day=to_day,
            hour=to_hour,
            minute=to_minute,
            second=now.second,
            tzinfo=pytz.timezone(time_zone)
        )

        return int((to - now).total_seconds() / 60)


class RespinaBaseModel(models.Model):
    class Meta:
        abstract = True

    serializer = None

    @classmethod
    def model_field_exists(cls, field):
        try:
            cls._meta.get_field(field)
            return True
        except models.FieldDoesNotExist:
            return False

    @classmethod
    def serialize(cls, request, queryset=None, is_list=True, one_object=None,
                  *args, **kwargs):
        return cls.serializer.serialize(request, queryset, is_list, one_object,
                                        *args, **kwargs)


class Operator:
    """
    Determine Number Operator by Test It on each Pattern.
    """

    class Codes:
        RESPINA = 'RSP'
        MCI = 'MCI'
        Irancell = 'MTN'
        RighTel = 'RighTel'
        TCT = 'TCT'
        LCT = 'LCT'

    class Labels:
        RSP = 'RSP_RESPINA_TEHRAN'
        MCI = 'RSP_MCI_TEHRAN'
        MTN = 'RSP_IRANCELL_TEHRAN'
        RighTel = 'RSP_RIGHTEL_TEHRAN'
        TCT = 'RSP_TCT_TEHRAN'
        LCT = 'RSP_LCT_TEHRAN'

    class DestinationTypes:
        CELL = 'cell'
        LAND = 'land'

    PATTERNS = (
        {
            Codes.RESPINA: (
                r'^([9821]|[021]|[21])*((9107|9200)[\d]{4})$',
                r'^(0|98)*((94260|94200)[\d]{5})$',
            )
        },
        {
            Codes.MCI: (
                r'^(98)9(1[0-9]|90)[0-9]+$',
            )
        },
        {
            Codes.Irancell: (
                r'^(98)9(3[0356789]|0[1235])[0-9]+$',
            )
        },
        {
            Codes.RighTel: (
                r'^(98)9(2|999|9810)[0-9]+$',
            )
        },
        {
            Codes.TCT: (
                r'^(9821).*$',
                r'^(94260|94200)[0-9]{5}$',
            )
        },
        {
            Codes.LCT: (

            )
        },
    )

    @classmethod
    def whois(cls, number):
        try:
            number = re.search(r'\d+', str(number)).group()
        except (ValueError, AttributeError):
            return None

        for operator in cls.PATTERNS:
            for code, patterns in operator.items():
                for p in patterns:
                    if re.match(p, number):
                        return {
                            'code': code,
                            'label': getattr(cls.Labels, code, None),
                        }
        return {
            'code': cls.Codes.LCT,
            'label': cls.Labels.LCT,
        }

    @classmethod
    def get_type(cls, number):
        if Operator.whois(number).get('code') in [Operator.Codes.MCI,
                                                  Operator.Codes.Irancell,
                                                  Operator.Codes.RighTel]:
            return Operator.DestinationTypes.CELL
        return Operator.DestinationTypes.LAND

    @classmethod
    def get_pattern(cls, operator_name):
        for opt in Operator.PATTERNS:
            for code, patterns in opt.items():
                if code == operator_name:
                    return patterns
