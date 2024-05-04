# SPDX-License-Identifier: AGPL-3.0-or-later
"""Processors for engine-type: ``online_currency``

"""

import re

from searx.data import fetch_iso4217_from_user, fetch_name_from_iso4217
from .online import OnlineProcessor

parser_re = re.compile('.*?(\\d+(?:\\.\\d+)?) ([^.0-9]+) (?:in|to) ([^.0-9]+)', re.I)


class OnlineCurrencyProcessor(OnlineProcessor):
    """Processor class used by ``online_currency`` engines."""

    engine_type = 'online_currency'

    def get_params(self, search_query, engine_category):
        """Returns a set of :ref:`request params <engine request online_currency>`
        or ``None`` if search query does not match to :py:obj:`parser_re`."""

        params = super().get_params(search_query, engine_category)
        if params is None:
            return None

        m = parser_re.match(search_query.query)
        if not m:
            return None

        amount_str, from_currency, to_currency = m.groups()
        try:
            amount = float(amount_str)
        except ValueError:
            return None
        from_currency = fetch_iso4217_from_user(from_currency.strip())
        to_currency = fetch_iso4217_from_user(to_currency.strip())

        if from_currency is None or to_currency is None:
            return None

        params['amount'] = amount
        params['from'] = from_currency
        params['to'] = to_currency
        params['from_name'] = fetch_name_from_iso4217(from_currency, 'en')
        params['to_name'] = fetch_name_from_iso4217(to_currency, 'en')
        return params

    def get_default_tests(self):
        tests = {}

        tests['currency'] = {
            'matrix': {'query': '1337 usd in rmb'},
            'result_container': ['has_answer'],
        }

        return tests
