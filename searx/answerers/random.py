# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations

import hashlib
import random
import string
import uuid
from flask_babel import gettext

from searx.result_types import Answer
from searx.result_types.answer import BaseAnswer

from . import Answerer, AnswererInfo


def random_characters():
    random_string_letters = string.ascii_lowercase + string.digits + string.ascii_uppercase
    return [random.choice(random_string_letters) for _ in range(random.randint(8, 32))]


def random_string():
    return ''.join(random_characters())


def random_float():
    return str(random.random())


def random_int():
    random_int_max = 2**31
    return str(random.randint(-random_int_max, random_int_max))


def random_sha256():
    m = hashlib.sha256()
    m.update(''.join(random_characters()).encode())
    return str(m.hexdigest())


def random_uuid():
    return str(uuid.uuid4())


def random_color():
    color = "%06x" % random.randint(0, 0xFFFFFF)
    return f"#{color.upper()}"


class SXNGAnswerer(Answerer):
    """Random value generator"""

    keywords = ["random"]

    random_types = {
        "string": random_string,
        "int": random_int,
        "float": random_float,
        "sha256": random_sha256,
        "uuid": random_uuid,
        "color": random_color,
    }

    def info(self):

        return AnswererInfo(
            name=gettext(self.__doc__),
            description=gettext("Generate different random values"),
            keywords=self.keywords,
            examples=[f"random {x}" for x in self.random_types],
        )

    def answer(self, query: str) -> list[BaseAnswer]:

        parts = query.split()
        if len(parts) != 2 or parts[1] not in self.random_types:
            return []

        return [Answer(answer=self.random_types[parts[1]]())]
