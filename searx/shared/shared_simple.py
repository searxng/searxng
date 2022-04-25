# SPDX-License-Identifier: AGPL-3.0-or-later

import threading
from typing import Optional

from . import shared_abstract


class SimpleSharedDict(shared_abstract.SharedDict):

    __slots__ = ('d',)

    def __init__(self):
        self.d = {}

    def get_int(self, key: str) -> Optional[int]:
        return self.d.get(key, None)

    def set_int(self, key: str, value: int, expire: Optional[int] = None):
        self.d[key] = value
        if expire:
            self._expire(key, expire)

    def get_str(self, key: str) -> Optional[str]:
        return self.d.get(key, None)

    def set_str(self, key: str, value: str, expire: Optional[int] = None):
        self.d[key] = value
        if expire:
            self._expire(key, expire)

    def _expire(self, key: str, expire: int):
        t = threading.Timer(expire, lambda k, d: d.pop(k), args=[key, self.d])
        t.daemon = True
        t.start()


def run_locked(func, *args):
    # SimpleSharedDict is not actually shared, so no locking needed
    return func(*args)


def schedule(delay, func, *args):
    def call_later():
        t = threading.Timer(delay, wrapper)
        t.daemon = True
        t.start()

    def wrapper():
        call_later()
        func(*args)

    call_later()
    return True
