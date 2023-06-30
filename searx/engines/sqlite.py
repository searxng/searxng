# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""SQLite is a small, fast and reliable SQL database engine.  It does not require
any extra dependency.

Example
=======

.. _MediathekView: https://mediathekview.de/

To demonstrate the power of database engines, here is a more complex example
which reads from a MediathekView_ (DE) movie database.  For this example of the
SQlite engine download the database:

- https://liste.mediathekview.de/filmliste-v2.db.bz2

and unpack into ``searx/data/filmliste-v2.db``.  To search the database use e.g
Query to test: ``!mediathekview concert``

.. code:: yaml

   - name: mediathekview
     engine: sqlite
     disabled: False
     categories: general
     result_template: default.html
     database: searx/data/filmliste-v2.db
     query_str:  >-
       SELECT title || ' (' || time(duration, 'unixepoch') || ')' AS title,
              COALESCE( NULLIF(url_video_hd,''), NULLIF(url_video_sd,''), url_video) AS url,
              description AS content
         FROM film
        WHERE title LIKE :wildcard OR description LIKE :wildcard
        ORDER BY duration DESC

Implementations
===============

"""

import sqlite3
import contextlib

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


@contextlib.contextmanager
def sqlite_cursor():
    """Implements a :py:obj:`Context Manager <contextlib.contextmanager>` for a
    :py:obj:`sqlite3.Cursor`.

    Open database in read only mode: if the database doesn't exist.  The default
    mode creates an empty file on the file system.  See:

    * https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
    * https://www.sqlite.org/uri.html

    """
    uri = 'file:' + database + '?mode=ro'
    with contextlib.closing(sqlite3.connect(uri, uri=True)) as connect:
        connect.row_factory = sqlite3.Row
        with contextlib.closing(connect.cursor()) as cursor:
            yield cursor


def search(query, params):
    results = []

    query_params = {
        'query': query,
        'wildcard': r'%' + query.replace(' ', r'%') + r'%',
        'limit': limit,
        'offset': (params['pageno'] - 1) * limit,
    }
    query_to_run = query_str + ' LIMIT :limit OFFSET :offset'

    with sqlite_cursor() as cur:

        cur.execute(query_to_run, query_params)
        col_names = [cn[0] for cn in cur.description]

        for row in cur.fetchall():
            item = dict(zip(col_names, map(str, row)))
            item['template'] = result_template
            logger.debug("append result --> %s", item)
            results.append(item)

    return results
