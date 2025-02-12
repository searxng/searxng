# SPDX-License-Identifier: AGPL-3.0-or-later
"""This provides an easy to use interface for engine implementations to store and read key-value pairs.

For instance, this can be used to remember programmatically extracted API keys or other kinds of secret tokens.
"""

from typing import Optional
from searx import redisdb, redislib


class EngineCache:
    def store(self, key: str, value: str):
        pass

    def get(self, key: str) -> Optional[str]:
        pass


class MemoryEngineCache(EngineCache):
    def __init__(self, max_size: int = 100):
        self.__STORAGE = {}
        self.max_size = max_size

    def store(self, key, value):
        """Store the provided key-value pair in the cache."""
        if len(self.__STORAGE) > self.max_size:
            self.__STORAGE.popitem()

        # remove the old value in order to add the new value to the top
        # of the dictionary, as dictionaries are ordered since Python 3.7
        if key in self.__STORAGE:
            self.__STORAGE.pop(key)

        self.__STORAGE[key] = value

    def get(self, key):
        return self.__STORAGE.get(key)


class RedisEngineCache(EngineCache):
    def __init__(self, key_prefix: str, expiration_seconds: int = 600):
        self.key_prefix = key_prefix
        self.expiration_seconds = expiration_seconds

    def _get_cache_key(self, key):
        return self.key_prefix + redislib.secret_hash(key)

    def store(self, key, value):
        c = redisdb.client()

        cache_key = self._get_cache_key(key)
        c.set(cache_key, value, ex=self.expiration_seconds)

    def get(self, key):
        c = redisdb.client()

        cache_key = self._get_cache_key(key)
        value = c.get(cache_key)
        if value or value == b'':
            return value

        return None


def get_or_create_cache(database_prefix: str) -> EngineCache:
    if redisdb.client():
        return RedisEngineCache(database_prefix)

    return MemoryEngineCache()
