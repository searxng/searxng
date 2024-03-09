# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations
from functools import reduce
from operator import mul

from flask_babel import gettext
from typing import Callable
from searx.answerers.models import AnswerDict, AnswerSelfInfoDict
from searx.search.models import BaseQuery


keywords = ('min', 'max', 'avg', 'sum', 'prod')


stastistics_map: dict[str, Callable[[list[float]], float]] = {
    'min': lambda args: min(args),
    'max': lambda args: max(args),
    'avg': lambda args: sum(args) / len(args),
    'sum': lambda args: sum(args),
    'prod': lambda args: reduce(mul, args, 1),
}


# required answerer function
# can return a list of results (any result type) for a given query
def answer(query: BaseQuery) -> list[AnswerDict]:
    parts = query.query.split()

    if len(parts) < 2:
        return []

    try:
        args: list[float] = list(map(float, parts[1:]))
    except Exception:
        return []

    func = parts[0]

    if func not in stastistics_map:
        return []

    return [{'answer': str(stastistics_map[func](args))}]


# required answerer function
# returns information about the answerer
def self_info() -> AnswerSelfInfoDict:
    return {
        'name': gettext('Statistics functions'),
        'description': gettext('Compute {functions} of the arguments').format(functions='/'.join(keywords)),
        'examples': ['avg 123 548 2.04 24.2'],
    }
