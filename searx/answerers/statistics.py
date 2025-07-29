# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring
from __future__ import annotations

from functools import reduce
from operator import mul

import babel
import babel.numbers
from flask_babel import gettext

from searx.extended_types import sxng_request
from searx.result_types import Answer
from searx.result_types.answer import BaseAnswer

from . import Answerer, AnswererInfo

kw2func = [
    ("min", min),
    ("max", max),
    ("avg", lambda args: sum(args) / len(args)),
    ("sum", sum),
    ("prod", lambda args: reduce(mul, args, 1)),
    ("range", lambda args: max(args) - min(args)),
]


class SXNGAnswerer(Answerer):
    """Statistics functions"""

    keywords = [kw for kw, _ in kw2func]

    def info(self):

        return AnswererInfo(
            name=gettext(self.__doc__),
            description=gettext("Compute {func} of the arguments".format(func='/'.join(self.keywords))),
            keywords=self.keywords,
            examples=["avg 123 548 2.04 24.2"],
        )

    def answer(self, query: str) -> list[BaseAnswer]:

        results = []
        parts = query.split()
        if len(parts) < 2:
            return results

        ui_locale = babel.Locale.parse(sxng_request.preferences.get_value('locale'), sep='-')

        try:
            args = [babel.numbers.parse_decimal(num, ui_locale, numbering_system="latn") for num in parts[1:]]
        except:  # pylint: disable=bare-except
            # seems one of the args is not a float type, can't be converted to float
            return results

        for k, func in kw2func:
            if k == parts[0]:
                res = func(args)
                res = babel.numbers.format_decimal(res, locale=ui_locale)
                f_str = ', '.join(babel.numbers.format_decimal(arg, locale=ui_locale) for arg in args)
                results.append(Answer(answer=f"[{ui_locale}] {k}({f_str}) = {res} "))
                break

        return results
