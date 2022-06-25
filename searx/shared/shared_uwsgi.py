# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import time
from typing import Optional, Tuple, Union
import uwsgi  # pyright: ignore # pylint: disable=E0401
from . import shared_abstract


_last_signal = 10


class UwsgiCacheSharedDict(shared_abstract.SharedDict):
    def get_int(self, key: str) -> Optional[int]:
        value, _, _ = self._get_value(key)
        if value is None:
            return value
        else:
            return int(value)

    def set_int(self, key: str, value: int, expire: Optional[int] = None):
        self._set_value(key, value, expire)

    def get_str(self, key: str) -> Optional[str]:
        value, _, _ = self._get_value(key)
        if value is None:
            return value
        else:
            return str(value)

    def set_str(self, key: str, value: str, expire: Optional[int] = None):
        self._set_value(key, value, expire)

    def _get_value(self, key: str) -> Tuple[Optional[Union[str, int]], Optional[float], Optional[int]]:
        serialized_data = uwsgi.cache_get(key)
        if not serialized_data:
            return None, None, None
        else:
            data = json.loads(serialized_data.decode())
            if 'expire' in data:
                now = time.time()
                if now - data['created_at'] >= data['expire']:
                    uwsgi.cache_del(key)
                    return None, None, None
            return data.get('value'), data.get('created_at'), data.get('expire')

    def _set_value(self, key: str, value: Union[str, int], expire: Optional[int] = None):
        _, created_at, original_expire = self._get_value(key)

        data = {'value': value}
        if expire is None and created_at is None:
            serialized_data = json.dumps(data).encode()
            uwsgi.cache_update(key, serialized_data)
        else:
            data['created_at'] = created_at or time.time()
            data['expire'] = original_expire or expire
            serialized_data = json.dumps(data).encode()
            uwsgi.cache_update(key, serialized_data, expire)


def run_locked(func, *args):
    result = None
    uwsgi.lock()
    try:
        result = func(*args)
    finally:
        uwsgi.unlock()
    return result


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
