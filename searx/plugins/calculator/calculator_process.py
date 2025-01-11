# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standalone script to actually calculate mathematical expressions using ast

This is not a module, the SearXNG modules are not available here
"""

import ast
import sys
import operator
from typing import Callable


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


def main():
    print(_eval_expr(sys.argv[1]), end="")


if __name__ == "__main__":
    main()
