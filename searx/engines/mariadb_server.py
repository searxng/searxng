# SPDX-License-Identifier: AGPL-3.0-or-later
"""MariaDB is a community driven fork of MySQL. Before enabling MariaDB engine,
you must the install the pip package ``mariadb`` along with the necessary
prerequities.

`See the following documentation for more details
<https://mariadb.com/docs/server/connect/programming-languages/c/install/>`_

Example
=======

This is an example configuration for querying a MariaDB server:

.. code:: yaml

   - name: my_database
     engine: mariadb_server
     database: my_database
     username: searxng
     password: password
     limit: 5
     query_str: 'SELECT * from my_table WHERE my_column=%(query)s'

Implementations
===============

"""

from typing import TYPE_CHECKING

try:
    import mariadb
except ImportError:
    # import error is ignored because the admin has to install mysql manually to use
    # the engine
    pass

if TYPE_CHECKING:
    import logging

    logger = logging.getLogger()


engine_type = 'offline'

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
result_template = 'key-value.html'
_connection = None


def init(engine_settings):
    global _connection  # pylint: disable=global-statement

    if 'query_str' not in engine_settings:
        raise ValueError('query_str cannot be empty')

    if not engine_settings['query_str'].lower().startswith('select '):
        raise ValueError('only SELECT query is supported')

    _connection = mariadb.connect(database=database, user=username, password=password, host=host, port=port)


def search(query, params):
    query_params = {'query': query}
    query_to_run = query_str + ' LIMIT {0} OFFSET {1}'.format(limit, (params['pageno'] - 1) * limit)
    logger.debug("SQL Query: %s", query_to_run)

    with _connection.cursor() as cur:
        cur.execute(query_to_run, query_params)
        results = []
        col_names = [i[0] for i in cur.description]
        for res in cur:
            result = dict(zip(col_names, map(str, res)))
            result['template'] = result_template
            results.append(result)
        return results
