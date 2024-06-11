# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from functools import reduce
from operator import mul

from flask_babel import gettext


keywords = ('min', 'max', 'avg', 'sum', 'prod')


# required answerer function
# can return a list of results (any result type) for a given query
def answer(query):
    parts = query.query.split()

    if len(parts) < 2:
        return []

    try:
        args = list(map(float, parts[1:]))
    except:  # pylint: disable=bare-except
        return []

    func = parts[0]
    _answer = None

    if func == 'min':
        _answer = min(args)
    elif func == 'max':
        _answer = max(args)
    elif func == 'avg':
        _answer = sum(args) / len(args)
    elif func == 'sum':
        _answer = sum(args)
    elif func == 'prod':
        _answer = reduce(mul, args, 1)

    if _answer is None:
        return []

    return [{'answer': str(_answer)}]


# required answerer function
# returns information about the answerer
def self_info():
    return {
        'name': gettext('Statistics functions'),
        'description': gettext('Compute {functions} of the arguments').format(functions='/'.join(keywords)),
        'examples': ['avg 123 548 2.04 24.2'],
    }
