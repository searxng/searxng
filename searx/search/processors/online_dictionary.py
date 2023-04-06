# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Processores for engine-type: ``online_dictionary``

"""

import re

from searx.utils import is_valid_lang
from .online import OnlineProcessor

parser_re = re.compile('.*?([a-z]+)-([a-z]+) (.+)$', re.I)


class OnlineDictionaryProcessor(OnlineProcessor):
    """Processor class used by ``online_dictionary`` engines."""

    engine_type = 'online_dictionary'

    def get_params(self, search_query, engine_category):
        """Returns a set of :ref:`request params <engine request online_dictionary>` or
        ``None`` if search query does not match to :py:obj:`parser_re`.
        """
        params = super().get_params(search_query, engine_category)
        if params is None:
            return None

        m = parser_re.match(search_query.query)
        if not m:
            return None

        from_lang, to_lang, query = m.groups()

        from_lang = is_valid_lang(from_lang)
        to_lang = is_valid_lang(to_lang)

        if not from_lang or not to_lang:
            return None

        params['from_lang'] = from_lang
        params['to_lang'] = to_lang
        params['query'] = query

        return params

    def get_default_tests(self):
        tests = {}

        if getattr(self.engine, 'paging', False):
            tests['translation_paging'] = {
                'matrix': {'query': 'en-es house', 'pageno': (1, 2, 3)},
                'result_container': ['not_empty', ('one_title_contains', 'house')],
                'test': ['unique_results'],
            }
        else:
            tests['translation'] = {
                'matrix': {'query': 'en-es house'},
                'result_container': ['not_empty', ('one_title_contains', 'house')],
            }

        return tests
