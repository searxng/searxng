# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: strict
"""Module implements a :py:class:`shared_abstract.SharedDict` to store data in a
redis DB (:py:obj:`redisdb`)."""

from typing import Optional
from . import shared_abstract
from . import redisdb

class RedisCacheSharedDict(shared_abstract.SharedDict):
    """Store key/value in the redis DB, the default prefix of the key in the DB is
    ``SearXNG_SharedDict`` (see :py.obj:`searx.redislib.purge_by_prefix`)."""

    def __init__(self, key_prefix='SearXNG_SharedDict'):
        self.key_prefix = key_prefix

    def get_int(self, key: str) -> Optional[int]:
        return int(redisdb.client().get(self.key_prefix + key))

    def set_int(self, key: str, value: int):
        redisdb.client().set(self.key_prefix + key, str(value).encode())

    def get_str(self, key: str) -> Optional[str]:
        value = redisdb.client().get(self.key_prefix + key)
        return None if value is None else value.decode()

    def set_str(self, key: str, value: str):
        redisdb.client().set(self.key_prefix + key, value.encode())
