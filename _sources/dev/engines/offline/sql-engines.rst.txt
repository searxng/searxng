.. _sql engines:

===========
SQL Engines
===========

.. sidebar:: further read

   - `SQLite <https://www.sqlite.org/index.html>`_
   - `PostgreSQL <https://www.postgresql.org>`_
   - `MySQL <https://www.mysql.com>`_

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

.. sidebar:: info

   Initial sponsored by `Search and Discovery Fund
   <https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.

With the *SQL engines* you can bind SQL databases into SearXNG.  The following
Relational Database Management System (RDBMS) are supported:

- :ref:`engine sqlite`
- :ref:`engine postgresql`
- :ref:`engine mysql_server` & :ref:`engine mariadb_server`

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


Extra Dependencies
==================

For using :ref:`engine postgresql` or :ref:`engine mysql_server` you need to
install additional packages in Python's Virtual Environment of your SearXNG
instance.  To switch into the environment (:ref:`searxng-src`) you can use
:ref:`searxng.sh`::

  $ sudo utils/searxng.sh instance cmd bash
  (searxng-pyenv)$ pip install ...


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

.. automodule:: searx.engines.sqlite
  :members:


.. _engine postgresql:

PostgreSQL
----------

.. _psycopg2: https://www.psycopg.org/install

.. sidebar:: info

   - :origin:`postgresql.py <searx/engines/postgresql.py>`
   - ``pip install`` `psycopg2-binary <psycopg2>`_

.. automodule:: searx.engines.postgresql
  :members:

.. _engine mysql_server:

MySQL
-----

.. sidebar:: info

   - :origin:`mysql_server.py <searx/engines/mysql_server.py>`
   - ``pip install`` :pypi:`mysql-connector-python <mysql-connector-python>`


.. automodule:: searx.engines.mysql_server
  :members:

.. _engine mariadb_server:

MariaDB
--------

.. sidebar:: info

   - :origin:`mariadb_server.py <searx/engines/mariadb_server.py>`
   - ``pip install`` :pypi:`mariadb <mariadb>`


.. automodule:: searx.engines.mariadb_server
  :members:
