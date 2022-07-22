.. _sql engines:

===========
SQL Engines
===========

.. sidebar:: further read

   - `SQLite <https://www.sqlite.org/index.html>`_
   - `PostgreSQL <https://www.postgresql.org>`_
   - `MySQL <https://www.mysql.com>`_

With the *SQL engines* you can bind SQL databases into SearXNG.  The following
Relational Database Management System (RDBMS) are supported:

- :ref:`engine sqlite`
- :ref:`engine postgresql`
- :ref:`engine mysql_server`

All of the engines above are just commented out in the :origin:`settings.yml
<searx/settings.yml>`, as you have to set the required attributes for the
engines, e.g. ``database:`` ...

.. code:: yaml

   - name: ...
     engine: {sqlite|postgresql|mysql_server}
     database: ...
     result_template: {template_name}
     query_str: ...

By default, the engines use the ``key-value`` template for displaying results /
see :origin:`simple <searx/templates/simple/result_templates/key-value.html>`
theme.  If you are not satisfied with the original result layout, you can use
your own template, set ``result_template`` attribute to ``{template_name}`` and
place the templates at::

  searx/templates/{theme_name}/result_templates/{template_name}

If you do not wish to expose these engines on a public instance, you can still
add them and limit the access by setting ``tokens`` as described in section
:ref:`private engines`.


Configure the engines
=====================

The configuration of the new database engines are similar.  You must put a valid
SQL-SELECT query in ``query_str``.  At the moment you can only bind at most one
parameter in your query.  By setting the attribute ``limit`` you can define how
many results you want from the SQL server.  Basically, it is the same as the
``LIMIT`` keyword in SQL.

Please, do not include ``LIMIT`` or ``OFFSET`` in your SQL query as the engines
rely on these keywords during paging.  If you want to configure the number of
returned results use the option ``limit``.

.. _engine sqlite:

SQLite
------

.. sidebar:: info

   - :origin:`sqlite.py <searx/engines/sqlite.py>`

.. _MediathekView: https://mediathekview.de/

SQLite is a small, fast and reliable SQL database engine.  It does not require
any extra dependency.  To demonstrate the power of database engines, here is a
more complex example which reads from a MediathekView_ (DE) movie database.  For
this example of the SQlite engine download the database:

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


Extra Dependencies
------------------

For using :ref:`engine postgresql` or :ref:`engine mysql_server` you need to
install additional packages in Python's Virtual Environment of your SearXNG
instance.  To switch into the environment (:ref:`searxng-src`) you can use
:ref:`searxng.sh`::

  $ sudo utils/searxng.sh instance cmd bash
  (searxng-pyenv)$ pip install ...


.. _engine postgresql:

PostgreSQL
----------

.. _psycopg2: https://www.psycopg.org/install

.. sidebar:: info

   - :origin:`postgresql.py <searx/engines/postgresql.py>`
   - ``pip install`` psycopg2_

PostgreSQL is a powerful and robust open source database.  Before configuring
the PostgreSQL engine, you must install the dependency ``psychopg2``.  You can
find an example configuration below:

.. code:: yaml

   - name: my_database
     engine: postgresql
     database: my_database
     username: searxng
     password: password
     query_str: 'SELECT * from my_table WHERE my_column = %(query)s'

.. _engine mysql_server:

MySQL
-----

.. sidebar:: info

   - :origin:`mysql_server.py <searx/engines/mysql_server.py>`
   - ``pip install`` :pypi:`mysql-connector-python <mysql-connector-python>`

MySQL is said to be the most popular open source database. Before enabling MySQL
engine, you must install the package ``mysql-connector-python``.

The authentication plugin is configurable by setting ``auth_plugin`` in the
attributes.  By default it is set to ``caching_sha2_password``.  This is an
example configuration for quering a MySQL server:

.. code:: yaml

   - name: my_database
     engine: mysql_server
     database: my_database
     username: searxng
     password: password
     limit: 5
     query_str: 'SELECT * from my_table WHERE my_column=%(query)s'


Acknowledgment
==============

This development was sponsored by `Search and Discovery Fund
<https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.

