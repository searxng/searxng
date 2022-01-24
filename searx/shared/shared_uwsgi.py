# SPDX-License-Identifier: AGPL-3.0-or-later

import time
from typing import Optional
import uwsgi  # pylint: disable=E0401
from . import shared_abstract


_last_signal = 10


class UwsgiCacheSharedDict(shared_abstract.SharedDict):
    def get_int(self, key: str) -> Optional[int]:
        value = uwsgi.cache_get(key)
        if value is None:
            return value
        else:
            return int.from_bytes(value, 'big')

    def set_int(self, key: str, value: int):
        b = value.to_bytes(4, 'big')
        uwsgi.cache_update(key, b)

    def get_str(self, key: str) -> Optional[str]:
        value = uwsgi.cache_get(key)
        if value is None:
            return value
        else:
            return value.decode('utf-8')

    def set_str(self, key: str, value: str):
        b = value.encode('utf-8')
        uwsgi.cache_update(key, b)


def schedule(delay, func, *args):
    """
    Can be implemented using a spooler.
    https://uwsgi-docs.readthedocs.io/en/latest/PythonDecorators.html

    To make the uwsgi configuration simple, use the alternative implementation.
    """
    global _last_signal

    def sighandler(signum):
        now = int(time.time())
        key = 'scheduler_call_time_signal_' + str(signum)
        uwsgi.lock()
        try:
            updating = uwsgi.cache_get(key)
            if updating is not None:
                updating = int.from_bytes(updating, 'big')
                if now - updating < delay:
                    return
            uwsgi.cache_update(key, now.to_bytes(4, 'big'))
        finally:
            uwsgi.unlock()
        func(*args)

    signal_num = _last_signal
    _last_signal += 1
    uwsgi.register_signal(signal_num, 'worker', sighandler)
    uwsgi.add_timer(signal_num, delay)
    return True
