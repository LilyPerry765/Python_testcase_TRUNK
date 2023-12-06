from rest_framework.throttling import AnonRateThrottle


class AnonMinRateThrottle(AnonRateThrottle):
    rate = '15/min'
    scope = 'anon_min'


class AnonHourRateThrottle(AnonRateThrottle):
    rate = '50/hour'
    scope = 'anon_hour'


class AnonDayRateThrottle(AnonRateThrottle):
    rate = '300/day'
    scope = 'anon_day'
