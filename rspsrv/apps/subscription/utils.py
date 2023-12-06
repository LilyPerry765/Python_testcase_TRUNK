import re

from django.conf import settings

from rspsrv.tools.utility import Helper


def normalize_outbound_number(number, subscription_number=None):
    return number


def is_number_international(number):
    if not number:
        return True
    pattern = r'^((00' + settings.COUNTRY_CODE + r'|\+' + \
              settings.COUNTRY_CODE + r'){0,1})0{0,1}[1-9][\d]*'
    pattern = re.compile(pattern)
    if not pattern.match(number):
        return True
    return False


# noinspection PyBroadException
def abnormal_subscription_number(number):
    result = re.search(r'^(0|\+98|98)?([\d]{10})', number)

    try:
        return result.group(2)
    except Exception:
        return None


def get_pure_number(number):
    """
    e.g: For '02191072323' number returns '91072323'.
    :param number:
    :return:
    """
    if not number or not isinstance(number, str):
        return None

    pattern = r'([\d]{2,})?((9107|9200)[\d]{4})$'
    groups = re.search(pattern, number)

    if groups:
        return groups.group(2)

    pattern = r'([\d]{2,})?((94260|94200)[\d]{5})$'
    groups = re.search(pattern, number)

    if groups:
        return groups.group(2)

    return None


def get_number(number):
    return Helper.normalize_number(
        number=number,
    )
