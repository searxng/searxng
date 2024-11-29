# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calculate mathematical expressions using ack#eval
"""

import ast
import re
import operator
from multiprocessing import Process, Queue
from typing import Callable

import flask
import babel
from flask_babel import gettext

from searx.plugins import logger

name = "Basic Calculator"
description = gettext("Calculate mathematical expressions via the search bar")
default_on = True

preference_section = 'general'
plugin_id = 'calculator'

logger = logger.getChild(plugin_id)

operators: dict[type, Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg,
}


def _eval_expr(expr):
    """
    >>> _eval_expr('2^6')
    4
    >>> _eval_expr('2**6')
    64
    >>> _eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    try:
        return _eval(ast.parse(expr, mode='eval').body)
    except ZeroDivisionError:
        # This is undefined
        return ""


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp):
        return operators[type(node.op)](_eval(node.left), _eval(node.right))

    if isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](_eval(node.operand))

    raise TypeError(node)


def timeout_func(timeout, func, *args, **kwargs):

    def handler(q: Queue, func, args, **kwargs):  # pylint:disable=invalid-name
        try:
            q.put(func(*args, **kwargs))
        except:
            q.put(None)
            raise

    que = Queue()
    p = Process(target=handler, args=(que, func, args), kwargs=kwargs)
    p.start()
    p.join(timeout=timeout)
    ret_val = None
    if not p.is_alive():
        ret_val = que.get()
    else:
        logger.debug("terminate function after timeout is exceeded")
        p.terminate()
    p.join()
    p.close()
    return ret_val


def post_search(_request, search):

    # only show the result of the expression on the first page
    if search.search_query.pageno > 1:
        return True

    query = search.search_query.query
    # in order to avoid DoS attacks with long expressions, ignore long expressions
    if len(query) > 100:
        return True

    # replace commonly used math operators with their proper Python operator
    query = query.replace("x", "*").replace(":", "/")

    # use UI language
    ui_locale = babel.Locale.parse(flask.request.preferences.get_value('locale'), sep='-')

    # parse the number system in a localized way
    def _decimal(match: re.Match) -> str:
        val = match.string[match.start() : match.end()]
        val = babel.numbers.parse_decimal(val, ui_locale, numbering_system="latn")
        return str(val)

    decimal = ui_locale.number_symbols["latn"]["decimal"]
    group = ui_locale.number_symbols["latn"]["group"]
    query = re.sub(f"[0-9]+[{decimal}|{group}][0-9]+[{decimal}|{group}]?[0-9]?", _decimal, query)

    # only numbers and math operators are accepted
    if any(str.isalpha(c) for c in query):
        return True

    # in python, powers are calculated via **
    query_py_formatted = query.replace("^", "**")

    # Prevent the runtime from being longer than 50 ms
    result = timeout_func(0.05, _eval_expr, query_py_formatted)
    if result is None or result == "":
        return True
    result = babel.numbers.format_decimal(result, locale=ui_locale)
    search.result_container.answers['calculate'] = {'answer': f"{search.search_query.query} = {result}"}
    return True
