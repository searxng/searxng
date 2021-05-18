# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring

"""SQLite database (Offline)

"""

import sqlite3

from searx import logger

logger = logger.getChild('SQLite engine')

engine_type = 'offline'
database = ""
query_str = ""
limit = 10
paging = True
result_template = 'key-value.html'

class SQLiteDB:
    """
    Implements a `Context Manager`_ for a SQLite.

    usage::

        with SQLiteDB('test.db') as cur:
            print(cur.execute('select sqlite_version();').fetchall()[0][0])

    .. _Context Manager: https://docs.python.org/3/library/stdtypes.html#context-manager-types
    """

    def __init__(self, db):
        self.database = db
        self.connect = None

    def __enter__(self):
        self.connect = sqlite3.connect(self.database)
        self.connect.row_factory = sqlite3.Row
        return self.connect.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connect.commit()
        self.connect.close()

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

    with SQLiteDB(database) as cur:

        cur.execute(query_to_run, query_params)
        col_names = [cn[0] for cn in cur.description]

        for row in cur.fetchall():
            item = dict( zip(col_names, map(str, row)) )
            item['template'] = result_template
            logger.debug("append result --> %s", item)
            results.append(item)

    return results
