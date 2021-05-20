# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring

"""SQLite database (Offline)

"""

from searx import logger
from searx.utils import SQLiteCursor

logger = logger.getChild('SQLite engine')

engine_type = 'offline'
database = ""
query_str = ""
limit = 10
paging = True
result_template = 'key-value.html'

def init(engine_settings):
    if 'query_str' not in engine_settings:
        raise ValueError('query_str cannot be empty')

    if not engine_settings['query_str'].lower().startswith('select '):
        raise ValueError('only SELECT query is supported')

def search(query, params):
    global database, query_str, result_template  # pylint: disable=global-statement
    results = []

    query_params = {
        'query': query,
        'wildcard':  r'%' + query.replace(' ',r'%') + r'%',
        'limit': limit,
        'offset': (params['pageno'] - 1) * limit
    }
    query_to_run = query_str + ' LIMIT :limit OFFSET :offset'

    with SQLiteCursor(database) as cur:

        cur.execute(query_to_run, query_params)
        col_names = [cn[0] for cn in cur.description]

        for row in cur.fetchall():
            item = dict( zip(col_names, map(str, row)) )
            item['template'] = result_template
            logger.debug("append result --> %s", item)
            results.append(item)

    return results
