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

    def set_int(self, key: str, value: int):
        self.d[key] = value

    def get_str(self, key: str) -> Optional[str]:
        return self.d.get(key, None)

    def set_str(self, key: str, value: str):
        self.d[key] = value


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
