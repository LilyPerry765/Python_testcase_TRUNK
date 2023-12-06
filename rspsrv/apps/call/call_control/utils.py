import re

from rspsrv.apps.extension.models import Extension


class NexfonNumberType:
    REGIONAL = 'regional'
    PORTABLE = 'portable'


def get_webapp(target_number):
    try:
        app = Extension.objects.get(number=target_number)
        return app
    except (Extension.DoesNotExist, Extension.MultipleObjectsReturned):
        pass


def number_is_regional(num):
    return bool(re.search(r"^(9107|9200)", num))


def number_is_portable(num):
    return bool(re.search(r"^(94260|94200)", num))


def get_nexfon_number_type(target_number):
    if number_is_regional(target_number):
        return NexfonNumberType.REGIONAL
    if number_is_portable(target_number):
        return NexfonNumberType.PORTABLE
    return None
