import math

from rspsrv.apps.cdr.models import CDR
from django.db.models import Q


def get_peak_hours(peak):
    return str(peak) + ':00:00', str(peak + 1) + ':00:00'


def compute_percent(arg1, arg2):
    if arg2 == 0:
        return 0
    return round(arg1/arg2 * 100, 1)


class NumberingCapacityService:
    @classmethod
    def get_asr1(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            (Q(called__startswith='+9821') | Q(
                called__iregex=r'^(\+98|0)*([0-9]{2})*(9107|9200|94260|94200)[0-9]+'
            )), call_odate=date,
            call_otime__range=(start, end)
        )
        ans = queryset.filter(talk_time__gt=0).count()
        sez = queryset.filter(duration__gt=0).count()
        return compute_percent(ans, sez)

    @classmethod
    def get_cer2(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(call_odate=date, call_otime__range=(start, end))
        sez = queryset.filter(duration__gt=0).count()
        bid = queryset.count()
        return compute_percent(sez, bid)

    @classmethod
    def get_asr3(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter((Q(
            called__iregex=r'^(\+98|0)*9(1[0-9]|9[0-3])[0-9]+') | Q(
            called__iregex=r'^(\+98|0)*9(3[0356789]|0[1235])[0-9]+') | Q(
            called__iregex=r'^(\+98|0)*92[0-9]+'
        )), call_odate=date, call_otime__range=(start, end))
        ans = queryset.filter(talk_time__gt=0).count()
        sez = queryset.filter(duration__gt=0).count()
        return compute_percent(ans, sez)

    @classmethod
    def get_poi4(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(call_odate=date, call_otime__range=(start, end))
        no_ans = queryset.filter(duration=0).count()
        bid = queryset.count()
        return compute_percent(no_ans, bid)

    @classmethod
    def get_asr5_land(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            call_odate=date,
            call_otime__range=(start, end)).filter(
            ~Q(called__startswith='+9821'),
            ~Q(called__startswith='+989'),
            ~Q(called__iregex=r'^(\+98|0)*([0-9]{2})*(9107|9200|94260|94200)[0-9]+'),
        )
        ans = queryset.filter(talk_time__gt=0).count()
        sez = queryset.filter(duration__gt=0).count()
        return compute_percent(ans, sez)

    @classmethod
    def get_asr5_cell(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            called__startswith='+989',
            call_odate=date,
            call_otime__range=(start, end)).filter(
            ~Q(called__iregex=r'^(\+98|0)*9(1[0-9]|9[0-3])[0-9]+'),
            ~Q(called__iregex=r'^(\+98|0)*9(3[0356789]|0[1235])[0-9]+'),
            ~Q(called__iregex=r'^(\+98|0)*92[0-9]+'),
        )
        ans = queryset.filter(talk_time__gt=0).count()
        sez = queryset.filter(duration__gt=0).count()
        return compute_percent(ans, sez)

    @classmethod
    def get_abr8_land(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            ~Q(called__startswith='+989'),
            call_odate=date,
            call_otime__range=(start, end))
        ans = queryset.filter(talk_time__gt=0).count()
        bid = queryset.count()
        return compute_percent(ans, bid)

    @classmethod
    def get_abr8_cell(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            called__startswith='+989',
            call_odate=date,
            call_otime__range=(start, end)
        )
        ans = queryset.filter(talk_time__gt=0).count()
        bid = queryset.count()
        return compute_percent(ans, bid)

    @classmethod
    def get_asr9_land(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            ~Q(called__startswith='+989'),
            call_odate=date,
            call_otime__range=(start, end))
        ans = queryset.filter(talk_time__gt=0).count()
        sez = queryset.filter(duration__gt=0).count()
        return compute_percent(ans, sez)

    @classmethod
    def get_asr9_cell(cls, date, peak):
        start, end = get_peak_hours(peak)
        queryset = CDR.objects.filter(
            called__startswith='+989',
            call_odate=date,
            call_otime__range=(start, end)
        )
        ans = queryset.filter(talk_time__gt=0).count()
        sez = queryset.filter(duration__gt=0).count()
        return compute_percent(ans, sez)
