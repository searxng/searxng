# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations
from typing import TypedDict, Tuple
from abc import abstractmethod, ABC
from searx.search.models import BaseQuery


class AnswerDict(TypedDict):
    """The result of a given answer response"""

    answer: str


class AnswerSelfInfoDict(TypedDict):
    """The information about the AnswerModule"""

    name: str
    description: str
    examples: list[str]


class AnswerModule(ABC):
    """A module which returns possible answers for auto-complete requests"""

    @property
    @abstractmethod
    def keywords(self) -> Tuple[str]:
        """Keywords which will be used to determine if the answer should be called"""

    @abstractmethod
    def answer(self, query: BaseQuery) -> list[AnswerDict]:
        """From a query, get the possible auto-complete answers"""

    @abstractmethod
    def self_info(self) -> AnswerSelfInfoDict:
        """Provides information about the AnswerModule"""
