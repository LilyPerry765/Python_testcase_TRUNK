# --------------------------------------------------------------------------
# Caching layer for dynamic keys. This class uses sha256 to generate keys
# and django's core caching system to store data.
# (C) 2019 Mehrdad Esmaeilpour, Tehran, Iran
# Respina Networks and beyonds - cache.py
# Created at 2020-08-09,  16:6:16
# Author: Mehrdad Esmaeilpour
# Email: m.esmailpour@respina.net
# --------------------------------------------------------------------------

import json
from hashlib import sha256

from django.core.cache import cache


class Cache:

    @classmethod
    def set(cls, key, values: dict, store_value, expiry_time=None):
        """
        Set new (key, value) an cache
        :param key:
        :param values:
        :param store_value:
        :param expiry_time: in seconds
        :return:
        """
        cache_key = cls._get_key(key, **values)
        cache.set(cache_key, store_value, expiry_time)

    @classmethod
    def get(cls, key, values: dict):
        cache_key = cls._get_key(key, **values)
        return cache.get(cache_key)

    @classmethod
    def delete(cls, key, values: dict):
        cache_key = cls._get_key(key, **values)
        cache.delete(cache_key)

    @classmethod
    def _get_key(cls, key, **kwargs):
        """
        Return sha256 hashed key to store in cache table
        :param kwargs: key value (dict)
        :return:
        """
        kwargs = json.dumps(kwargs)
        cache_key = sha256(
            str("{}:{}".format(key, kwargs)).encode('utf-8')
        )

        return cache_key.hexdigest()
