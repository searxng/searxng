# SPDX-License-Identifier: AGPL-3.0-or-later
# pyright: strict
from abc import ABC, abstractmethod
from typing import Optional


class SharedDict(ABC):

    def __init__(self, *args, **kwarg):
        pass

    @abstractmethod
    def get_int(self, key: str) -> Optional[int]:
        pass

    @abstractmethod
    def set_int(self, key: str, value: int):
        pass

    @abstractmethod
    def get_str(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_str(self, key: str, value: str):
        pass
