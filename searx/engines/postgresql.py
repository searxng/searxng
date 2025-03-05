# SPDX-License-Identifier: AGPL-3.0-or-later
"""PostgreSQL is a powerful and robust open source database.  Before configuring
the PostgreSQL engine, you must install the dependency ``psychopg2``.

Example
=======

Below is an example configuration:

.. code:: yaml

   - name: my_database
     engine: postgresql
     database: my_database
     username: searxng
     password: password
     query_str: 'SELECT * from my_table WHERE my_column = %(query)s'

Implementations
===============

"""

try:
    import psycopg2  # type: ignore
except ImportError:
    # import error is ignored because the admin has to install postgresql
    # manually to use the engine.
    pass

from searx.result_types import EngineResults

engine_type = 'offline'

host = "127.0.0.1"
"""Hostname of the DB connector"""

port = "5432"
"""Port of the DB connector"""

database = ""
"""Name of the database."""

username = ""
"""Username for the DB connection."""

password = ""
"""Password for the DB connection."""

query_str = ""
"""SQL query that returns the result items."""

limit = 10
paging = True
_connection = None


def init(engine_settings):
    global _connection  # pylint: disable=global-statement

    if 'query_str' not in engine_settings:
        raise ValueError('query_str cannot be empty')

    if not engine_settings['query_str'].lower().startswith('select '):
        raise ValueError('only SELECT query is supported')

    _connection = psycopg2.connect(
        database=database,
        user=username,
        password=password,
        host=host,
        port=port,
    )


def search(query, params) -> EngineResults:
    query_params = {'query': query}
    query_to_run = query_str + ' LIMIT {0} OFFSET {1}'.format(limit, (params['pageno'] - 1) * limit)

    with _connection:
        with _connection.cursor() as cur:
            cur.execute(query_to_run, query_params)
            return _fetch_results(cur)


def _fetch_results(cur) -> EngineResults:
    res = EngineResults()
    try:
        titles = [column_desc.name for column_desc in cur.description]
        for row in cur:
            kvmap = dict(zip(titles, map(str, row)))
            res.add(res.types.KeyValue(kvmap=kvmap))

    # no results to fetch
    except psycopg2.ProgrammingError:
        pass

    return res
