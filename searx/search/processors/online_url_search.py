# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Processores for engine-type: ``online_url_search``

"""

import re
from .online import OnlineProcessor

re_search_urls = {
    'http': re.compile(r'https?:\/\/[^ ]*'),
    'ftp': re.compile(r'ftps?:\/\/[^ ]*'),
    'data:image': re.compile('data:image/[^; ]*;base64,[^ ]*'),
}


class OnlineUrlSearchProcessor(OnlineProcessor):
    """Processor class used by ``online_url_search`` engines."""

    engine_type = 'online_url_search'

    def get_params(self, search_query, engine_category):
        params = super().get_params(search_query, engine_category)
        if params is None:
            return None

        url_match = False
        search_urls = {}

        for k, v in re_search_urls.items():
            m = v.search(search_query.query)
            v = None
            if m:
                url_match = True
                v = m[0]
            search_urls[k] = v

        if not url_match:
            return None

        params['search_urls'] = search_urls
        return params
