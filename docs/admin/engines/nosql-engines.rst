===============
NoSQL databases
===============

.. sidebar:: further read

   - `NoSQL databases <https://en.wikipedia.org/wiki/NoSQL>`_
   - `redis.io <https://redis.io/>`_
   - `MongoDB <https://www.mongodb.com>`_

The following `NoSQL databases`_ are supported:

- :ref:`engine redis_server`
- :ref:`engine mongodb`

All of the engines above are just commented out in the :origin:`settings.yml
<searx/settings.yml>`, as you have to set various options and install
dependencies before using them.

By default, the engines use the ``key-value`` template for displaying results /
see :origin:`simple <searx/templates/simple/result_templates/key-value.html>`
theme.  If you are not satisfied with the original result layout, you can use
your own template, set ``result_template`` attribute to ``{template_name}`` and
place the templates at::

  searx/templates/{theme_name}/result_templates/{template_name}

Futhermore, if you do not wish to expose these engines on a public instance, you
can still add them and limit the access by setting ``tokens`` as described in
section :ref:`private engines`.


Configure the engines
=====================

`NoSQL databases`_ are used for storing arbitrary data without first defining
their structure.


Extra Dependencies
------------------

For using :ref:`engine redis_server` or :ref:`engine mongodb` you need to
install additional packages in Python's Virtual Environment of your SearXNG
instance.  To switch into the environment (:ref:`searxng-src`) you can use
:ref:`searxng.sh`::

  $ sudo utils/searxng.sh instance cmd bash
  (searxng-pyenv)$ pip install ...


.. _engine redis_server:

Redis Server
------------

.. _redis: https://github.com/andymccurdy/redis-py#installation

.. sidebar:: info

   - ``pip install`` redis_
   - redis.io_
   - :origin:`redis_server.py <searx/engines/redis_server.py>`


Redis is an open source (BSD licensed), in-memory data structure (key value
based) store.  Before configuring the ``redis_server`` engine, you must install
the dependency redis_.

Select a database to search in and set its index in the option ``db``.  You can
either look for exact matches or use partial keywords to find what you are
looking for by configuring ``exact_match_only``.  You find an example
configuration below:

.. code:: yaml

  # Required dependency: redis

  - name: myredis
    shortcut : rds
    engine: redis_server
    exact_match_only: false
    host: '127.0.0.1'
    port: 6379
    enable_http: true
    password: ''
    db: 0

.. _engine mongodb:

MongoDB
-------

.. _pymongo: https://github.com/mongodb/mongo-python-driver#installation

.. sidebar:: info

   - ``pip install`` pymongo_
   - MongoDB_
   - :origin:`mongodb.py <searx/engines/mongodb.py>`

MongoDB_ is a document based database program that handles JSON like data.
Before configuring the ``mongodb`` engine, you must install the dependency
redis_.

In order to query MongoDB_, you have to select a ``database`` and a
``collection``.  Furthermore, you have to select a ``key`` that is going to be
searched.  MongoDB_ also supports the option ``exact_match_only``, so configure
it as you wish.  Below is an example configuration for using a MongoDB
collection:

.. code:: yaml

  # MongoDB engine
  # Required dependency: pymongo

  - name: mymongo
    engine: mongodb
    shortcut: md
    exact_match_only: false
    host: '127.0.0.1'
    port: 27017
    enable_http: true
    results_per_page: 20
    database: 'business'
    collection: 'reviews'  # name of the db collection
    key: 'name'            # key in the collection to search for


Acknowledgment
==============

This development was sponsored by `Search and Discovery Fund
<https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.

