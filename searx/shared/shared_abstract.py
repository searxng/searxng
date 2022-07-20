# SPDX-License-Identifier: AGPL-3.0-or-later
# pyright: strict
import hmac
from abc import ABC, abstractmethod
from typing import Optional

from searx import get_setting


class SharedDict(ABC):
    @abstractmethod
    def get_int(self, key: str) -> Optional[int]:
        pass

    @abstractmethod
    def set_int(self, key: str, value: int, expire: Optional[int] = None):
        pass

    @abstractmethod
    def get_str(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_str(self, key: str, value: str, expire: Optional[int] = None):
        pass

    def incr_counter(self, name: str, limit: int = 0, expire: int = 0) -> int:
        # generate dict key from name
        m = hmac.new(bytes(name, encoding='utf-8'), digestmod='sha256')
        m.update(bytes(get_setting('server.secret_key'), encoding='utf-8'))
        key = 'SearXNG_counter_' + m.hexdigest()

        # check requests count
        count = self.get_int(key)
        if count is None:
            # initialize counter with expiration time
            self.set_int(key, 1, expire)
            return 1
        elif limit >= count or not limit:
            # update counter
            new_count = count + 1
            self.set_int(key, new_count, expire)
            return new_count
        else:
            return count
