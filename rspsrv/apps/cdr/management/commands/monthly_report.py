import re

from django.core.management.base import BaseCommand
from khayyam import JalaliDatetime

from rspsrv.apps.cdr.models import CDR

operator = ['MCI', 'MTN', 'Rightel', 'LCT', 'TCT', 'RSPN']

mci_re = re.compile('^(98|0)*9(1[0-9]|90)[0-9]+')
mtn_re = re.compile('^(98|0)*9(3[0356789]|0[1235])[0-9]+')
rtl_re = re.compile('^(98|0)*9(2|999|9810)[0-9]+')
tct_re = re.compile('^(98|0)*(21)*[0-9]{8}$')
rsp_re = re.compile('^(98|0)*([0-9]{2})*(9107|9200|94260|94200)[0-9]+')

def get_operator(number):
    if mci_re.match(number):
        return 0
    if mtn_re.match(number):
        return 1
    if rtl_re.match(number):
        return 2
    if rsp_re.match(number):
        return 5
    if tct_re.match(number):
        return 4
    return 3


class Command(BaseCommand):
    help = 'Generates monthly reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            default=0,
            help='Defines persian month, 0 means current month',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=0,
            help='Defines persian month, 0 means current month',
        )

    def handle(self, *args, **options):
        month = options['month'] if options['month'] != 0 else JalaliDatetime.now().month
        year = options['year'] if options['year'] != 0 else JalaliDatetime.now().year
        cdrs = CDR.objects.filter(state='closed')
        result = list() 
        for r in range(13):
            result.append([0,0,[]])
        for cdr in cdrs:
            if JalaliDatetime(cdr.call_odate).month != month or JalaliDatetime(cdr.call_odate).year != year:
                continue
            if cdr.direction == 'inbound':
                row = 2*get_operator(cdr.caller)
                check = cdr.caller
            elif cdr.direction == 'outbound':
                row = 2*get_operator(cdr.called) + 1
                check = cdr.called
            elif cdr.direction == 'internal':
                row = 12
                check = cdr.called
            result[row][0] += int((cdr.talk_time + 59) / 60)
            if cdr.talk_time:
                result[row][1] += 1
                if check not in result[row][2]:
                    result[row][2].append(check)
      
        for r in result:
            r[0] = str(r[0])
            r[1] = str(r[1])
            r[2] = str(len(r[2]))
            print(",".join(r))

