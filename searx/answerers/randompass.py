# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import random
import string

from flask_babel import gettext

from searx.result_types import Answer
from searx.result_types.answer import BaseAnswer

from . import Answerer, AnswererInfo

DEFAULT_LENGTH = 16
MIN_LENGTH = 4
MAX_LENGTH = 128

CHARS = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"


def generate_password(length: int = DEFAULT_LENGTH) -> str:
    return "".join(random.choices(CHARS, k=length))


class SXNGAnswerer(Answerer):
    keywords = ["randompass", "randompassword"]

    def info(self) -> AnswererInfo:
        return AnswererInfo(
            name=gettext(self.__doc__),
            description=gettext("Generate a random password (optionally specify length)"),
            keywords=self.keywords,
            examples=["randompass", "randompass 24", "randompassword", "randompassword 24"],
        )

    def answer(self, query: str) -> list[BaseAnswer]:
        parts = query.split()
        if not parts or parts[0] not in self.keywords:
            return []

        length = DEFAULT_LENGTH
        if len(parts) >= 2:
            try:
                length = int(parts[1])
                length = max(MIN_LENGTH, min(MAX_LENGTH, length))
            except ValueError:
                pass

        return [Answer(answer=generate_password(length))]
