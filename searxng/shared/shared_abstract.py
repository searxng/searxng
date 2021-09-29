# SPDX-License-Identifier: AGPL-3.0-or-later
from abc import ABC, abstractmethod


class SharedDict(ABC):

    @abstractmethod
    def get_int(self, key):
        pass

    @abstractmethod
    def set_int(self, key, value):
        pass

    @abstractmethod
    def get_str(self, key):
        pass

    @abstractmethod
    def set_str(self, key, value):
        pass
