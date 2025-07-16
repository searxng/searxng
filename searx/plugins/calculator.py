# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calculate mathematical expressions using :py:obj:`ast.parse` (mode="eval")."""

from __future__ import annotations
import typing

import ast
import math
import re
import operator
import multiprocessing

import babel
import babel.numbers
from flask_babel import gettext

from searx.result_types import EngineResults
from searx.plugins import Plugin, PluginInfo

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg


class SXNGPlugin(Plugin):
    """Plugin converts strings to different hash digests.  The results are
    displayed in area for the "answers".
    """

    id = "calculator"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Basic Calculator"),
            description=gettext("Calculate mathematical expressions via the search bar"),
            preference_section="general",
        )

    def timeout_func(self, timeout, func, *args, **kwargs):
        que = mp_fork.Queue()
        p = mp_fork.Process(target=handler, args=(que, func, args), kwargs=kwargs)
        p.start()
        p.join(timeout=timeout)
        ret_val = None
        # pylint: disable=used-before-assignment,undefined-variable
        if not p.is_alive():
            ret_val = que.get()
        else:
            self.log.debug("terminate function (%s: %s // %s) after timeout is exceeded", func.__name__, args, kwargs)
            p.terminate()
        p.join()
        p.close()
        return ret_val

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        results = EngineResults()

        # only show the result of the expression on the first page
        if search.search_query.pageno > 1:
            return results

        query = search.search_query.query
        # in order to avoid DoS attacks with long expressions, ignore long expressions
        if len(query) > 100:
            return results

        # replace commonly used math operators with their proper Python operator
        query = query.replace("x", "*").replace(":", "/")

        # Is this a term that can be calculated?
        word, constants = "", set()
        for x in query:
            # Alphabetic characters are defined as "Letters" in the Unicode
            # character database and are the constants in an equation.
            if x.isalpha():
                word += x.strip()
            elif word:
                constants.add(word)
                word = ""

        # In the term of an arithmetic operation there should be no other
        # alphabetic characters besides the constants
        if constants - set(math_constants):
            return results

        # use UI language
        ui_locale = babel.Locale.parse(request.preferences.get_value("locale"), sep="-")

        # parse the number system in a localized way
        def _decimal(match: re.Match) -> str:
            val = match.string[match.start() : match.end()]
            val = babel.numbers.parse_decimal(val, ui_locale, numbering_system="latn")
            return str(val)

        decimal = ui_locale.number_symbols["latn"]["decimal"]
        group = ui_locale.number_symbols["latn"]["group"]
        query = re.sub(f"[0-9]+[{decimal}|{group}][0-9]+[{decimal}|{group}]?[0-9]?", _decimal, query)

        # in python, powers are calculated via **
        query_py_formatted = query.replace("^", "**")

        # Prevent the runtime from being longer than 50 ms
        res = self.timeout_func(0.05, _eval_expr, query_py_formatted)
        if res is None or res[0] == "":
            return results

        res, is_boolean = res
        if is_boolean:
            res = "True" if res != 0 else "False"
        else:
            res = babel.numbers.format_decimal(res, locale=ui_locale)
        results.add(results.types.Answer(answer=f"{search.search_query.query} = {res}"))

        return results


def _compare(ops: list[ast.cmpop], values: list[int | float]) -> int:
    """
    2 < 3 becomes ops=[ast.Lt] and values=[2,3]
    2 < 3 <= 4 becomes ops=[ast.Lt, ast.LtE] and values=[2,3, 4]
    """
    for op, a, b in zip(ops, values, values[1:]):  # pylint: disable=invalid-name
        if isinstance(op, ast.Eq) and a == b:
            continue
        if isinstance(op, ast.NotEq) and a != b:
            continue
        if isinstance(op, ast.Lt) and a < b:
            continue
        if isinstance(op, ast.LtE) and a <= b:
            continue
        if isinstance(op, ast.Gt) and a > b:
            continue
        if isinstance(op, ast.GtE) and a >= b:
            continue

        # Ignore impossible ops:
        # * ast.Is
        # * ast.IsNot
        # * ast.In
        # * ast.NotIn

        # the result is False for a and b and operation op
        return 0
    # the results for all the ops are True
    return 1


operators: dict[type, typing.Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.BitOr: operator.or_,
    ast.BitAnd: operator.and_,
    ast.USub: operator.neg,
    ast.RShift: operator.rshift,
    ast.LShift: operator.lshift,
    ast.Mod: operator.mod,
    ast.Compare: _compare,
}


math_constants = {
    'e': math.e,
    'pi': math.pi,
}


# with multiprocessing.get_context("fork") we are ready for Py3.14 (by emulating
# the old behavior "fork") but it will not solve the core problem of fork, nor
# will it remove the deprecation warnings in py3.12 & py3.13.  Issue is
# ddiscussed here: https://github.com/searxng/searxng/issues/4159
mp_fork = multiprocessing.get_context("fork")


def _eval_expr(expr):
    """
    Evaluates the given textual expression.

    Returns a tuple of (numericResult, isBooleanResult).

    >>> _eval_expr('2^6')
    64, False
    >>> _eval_expr('2**6')
    64, False
    >>> _eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0, False
    >>> _eval_expr('1 < 3')
    1, True
    >>> _eval_expr('5 < 3')
    0, True
    >>> _eval_expr('17 == 11+1+5 == 7+5+5')
    1, True
    """
    try:
        root_expr = ast.parse(expr, mode='eval').body
        return _eval(root_expr), isinstance(root_expr, ast.Compare)

    except (SyntaxError, TypeError, ZeroDivisionError):
        # Expression that can't be evaluated (i.e. not a math expression)
        return "", False


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp):
        return operators[type(node.op)](_eval(node.left), _eval(node.right))

    if isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](_eval(node.operand))

    if isinstance(node, ast.Compare):
        return _compare(node.ops, [_eval(node.left)] + [_eval(c) for c in node.comparators])

    if isinstance(node, ast.Name) and node.id in math_constants:
        return math_constants[node.id]

    raise TypeError(node)


def handler(q: multiprocessing.Queue, func, args, **kwargs):  # pylint:disable=invalid-name
    try:
        q.put(func(*args, **kwargs))
    except:
        q.put(None)
        raise
