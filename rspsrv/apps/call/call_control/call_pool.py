import logging

import redis
from django.conf import settings

from rspsrv.apps.subscription.models import Subscription

logger = logging.getLogger("call")


class LI(object):
    CIN = 0

    @staticmethod
    def increase_cin():
        LI.CIN += 1

    @staticmethod
    def get_cin():
        return str(LI.CIN)

    @staticmethod
    def issue_cin():
        LI.increase_cin()
        return LI.get_cin()


class CallDirection:
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


def remove_all_calls():
    global_redis = settings.GLOBAL_REDIS
    pool = redis.StrictRedis(
        host=global_redis['host'],
        port=global_redis['port'],
        db=global_redis['db'],
    )
    for subscription in Subscription.objects.all():
        pool.delete(subscription.number)


class Calls(object):
    global_redis = settings.GLOBAL_REDIS
    pool = redis.StrictRedis(host=global_redis['host'],
                             port=global_redis['port'],
                             db=global_redis['call_concurrency_db'])

    @staticmethod
    def set_call(number, direction):
        subscription_string = 'concurrency::{}::{}'.format(
            settings.CALL_CONCURRENCY_MACHINE_NAME,
            number
        )
        subscription_calls = Calls.pool.hgetall(
            subscription_string
        )

        if not bool(subscription_calls):
            Calls.pool.hset(
                subscription_string,
                CallDirection.INBOUND,
                0,
            )
            Calls.pool.hset(
                subscription_string,
                CallDirection.OUTBOUND,
                0,
            )

        Calls.pool.hincrby(
            subscription_string,
            direction,
        )

    @staticmethod
    def get_calls_by_direction(number, direction):
        subscription_calls = {b'inbound': 0, b'outbound': 0}

        for items in Calls.pool.scan(0, '*::{}'.format(number))[1]:
            switch_calls = Calls.pool.hgetall(items)
            switch_calls[b'inbound'] = int(switch_calls[b'inbound'])
            switch_calls[b'outbound'] = int(switch_calls[b'outbound'])

            subscription_calls = {
                k: switch_calls.get(k, 0) + subscription_calls.get(k, 0)
                for k in set(switch_calls) & set(subscription_calls)
            }

        calls = subscription_calls[direction.encode()]

        return calls

    @staticmethod
    def get_calls_by_number(number):
        inbound_calls = Calls.get_calls_by_direction(
            number,
            CallDirection.INBOUND,
        )
        outbound_calls = Calls.get_calls_by_direction(
            number,
            CallDirection.OUTBOUND
        )
        return inbound_calls + outbound_calls

    @staticmethod
    def remove_call(number, direction):
        subscription_string = 'concurrency::{}::{}'.format(
            settings.CALL_CONCURRENCY_MACHINE_NAME,
            number,
        )
        subscription_calls = Calls.pool.hgetall(subscription_string)

        if not bool(subscription_calls):
            return

        Calls.pool.hincrby(subscription_string, direction, -1)
