import logging
import threading

import redis
from django.conf import settings
from redis import RedisError

from rspsrv.apps.call.respina_ari import ari

# from ..local_settings import SWITCH_ARI, SWITCHMANAGER_APP_NAME

logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger("call")

CallPool = list()


def get_call_pool():
    return CallPool


class ARIManager(object):
    client = None
    worker = None
    cache_proxy_control = None
    cache_proxy_stack = None

    class ClientExists(Exception):
        pass

    class ProcessExists(Exception):
        pass

    class BillingCacheError(Exception):
        pass

    def __init__(self, client=None, worker=None):
        ARIManager.worker = worker
        ARIManager.client = client

    @staticmethod
    def st():
        if ARIManager.client is None:
            switch = settings.SWITCH_ARI[0]
            print("Connecting to: Host: %s User: %s Password: *****" % (switch['HOST'], switch['USER']))
            ARIManager.client = ari.connect(switch['HOST'], switch['USER'], switch['PASSWORD'])

        else:
            raise ARIManager.ClientExists

        if ARIManager.worker is None:
            print("Threading...")
            ARIManager.worker = threading.Thread(target=ARIManager.client.run,
                                                 args=(settings.SWITCHMANAGER_APP_NAME,))
            ARIManager.worker.start()
        else:
            raise ARIManager.ProcessExists

    @staticmethod
    def init_billing_cache_proxy():
        try:
            ARIManager.cache_proxy_control = redis.StrictRedis(host=settings.BILLING['core']['cache_proxy']['host'],
                                                               port=settings.BILLING['core']['cache_proxy']['port'],
                                                               db=settings.BILLING['core']['cache_proxy']['db'])
            ARIManager.cache_proxy_stack = ARIManager.cache_proxy_control.pubsub()
            ARIManager.cache_proxy_stack.subscribe(settings.BILLING['core']['cache_proxy']['channel'])

        except RedisError as e:
            logger.error(e)
            raise ARIManager.BillingCacheError


ARIDefaultManager = ARIManager()

# ARIDefaultManager.st()
