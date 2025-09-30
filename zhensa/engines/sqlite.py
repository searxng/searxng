# SPDX-License-Identifier: AGPL-3.0-or-later
"""SQLite is a small, fast and reliable SQL database engine.  It does not require
any extra dependency.

Configuration
=============

The engine has the following (additional) settings:

- :py:obj:`result_type`


Example
=======

.. _MediathekView: https://mediathekview.de/

To demonstrate the power of database engines, here is a more complex example
which reads from a MediathekView_ (DE) movie database.  For this example of the
SQLite engine download the database:

- https://liste.mediathekview.de/filmliste-v2.db.bz2

and unpack into ``zhensa/data/filmliste-v2.db``.  To search the database use e.g
Query to test: ``!mediathekview concert``

.. code:: yaml

  - name: mediathekview
    engine: sqlite
    shortcut: mediathekview
    categories: [general, videos]
    result_type: MainResult
    database: zhensa/data/filmliste-v2.db
    query_str: >-
      SELECT title || ' (' || time(duration, 'unixepoch') || ')' AS title,
             COALESCE( NULLIF(url_video_hd,''), NULLIF(url_video_sd,''), url_video) AS url,
             description AS content
        FROM film
       WHERE title LIKE :wildcard OR description LIKE :wildcard
       ORDER BY duration DESC

Implementations
===============

"""
import typing as t
import sqlite3
import contextlib

from zhensa.result_types import EngineResults
from zhensa.result_types import MainResult, KeyValue

engine_type = "offline"

database = ""
"""Filename of the SQLite DB."""

query_str = ""
"""SQL query that returns the result items."""

result_type: t.Literal["MainResult", "KeyValue"] = "KeyValue"
"""The result type can be :py:obj:`MainResult` or :py:obj:`KeyValue`."""

limit = 10
paging = True


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


def search(query, params) -> EngineResults:
    res = EngineResults()
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
            kvmap = dict(zip(col_names, map(str, row)))
            if result_type == "MainResult":
                item = MainResult(**kvmap)  # type: ignore
            else:
                item = KeyValue(kvmap=kvmap)
            res.add(item)

    return res
