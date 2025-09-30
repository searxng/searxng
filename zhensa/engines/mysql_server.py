# SPDX-License-Identifier: AGPL-3.0-or-later
"""MySQL is said to be the most popular open source database.  Before enabling
MySQL engine, you must install the package ``mysql-connector-python``.

The authentication plugin is configurable by setting ``auth_plugin`` in the
attributes.  By default it is set to ``caching_sha2_password``.

Example
=======

This is an example configuration for querying a MySQL server:

.. code:: yaml

   - name: my_database
     engine: mysql_server
     database: my_database
     username: zhensa
     password: password
     limit: 5
     query_str: 'SELECT * from my_table WHERE my_column=%(query)s'

Implementations
===============

"""

from zhensa.result_types import EngineResults

try:
    import mysql.connector  # type: ignore
except ImportError:
    # import error is ignored because the admin has to install mysql manually to use
    # the engine
    pass

engine_type = 'offline'
auth_plugin = 'caching_sha2_password'

host = "127.0.0.1"
"""Hostname of the DB connector"""

port = 3306
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

    _connection = mysql.connector.connect(
        database=database,
        user=username,
        password=password,
        host=host,
        port=port,
        auth_plugin=auth_plugin,
    )


def search(query, params) -> EngineResults:
    res = EngineResults()
    query_params = {'query': query}
    query_to_run = query_str + ' LIMIT {0} OFFSET {1}'.format(limit, (params['pageno'] - 1) * limit)

    with _connection.cursor() as cur:
        cur.execute(query_to_run, query_params)
        for row in cur:
            kvmap = dict(zip(cur.column_names, map(str, row)))
            res.add(res.types.KeyValue(kvmap=kvmap))

    return res
