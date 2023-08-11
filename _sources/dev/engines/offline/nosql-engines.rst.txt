.. _nosql engines:

===============
NoSQL databases
===============

.. sidebar:: further read

   - `NoSQL databases <https://en.wikipedia.org/wiki/NoSQL>`_
   - `redis.io <https://redis.io/>`_
   - `MongoDB <https://www.mongodb.com>`_

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

.. sidebar:: info

   Initial sponsored by `Search and Discovery Fund
   <https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.

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

Furthermore, if you do not wish to expose these engines on a public instance, you
can still add them and limit the access by setting ``tokens`` as described in
section :ref:`private engines`.


Extra Dependencies
==================

For using :ref:`engine redis_server` or :ref:`engine mongodb` you need to
install additional packages in Python's Virtual Environment of your SearXNG
instance.  To switch into the environment (:ref:`searxng-src`) you can use
:ref:`searxng.sh`::

  $ sudo utils/searxng.sh instance cmd bash
  (searxng-pyenv)$ pip install ...


Configure the engines
=====================

`NoSQL databases`_ are used for storing arbitrary data without first defining
their structure.


.. _engine redis_server:

Redis Server
------------

.. _redis: https://github.com/andymccurdy/redis-py#installation

.. sidebar:: info

   - ``pip install`` redis_
   - redis.io_
   - :origin:`redis_server.py <searx/engines/redis_server.py>`

.. automodule:: searx.engines.redis_server
  :members:


.. _engine mongodb:

MongoDB
-------

.. _pymongo: https://github.com/mongodb/mongo-python-driver#installation

.. sidebar:: info

   - ``pip install`` pymongo_
   - MongoDB_
   - :origin:`mongodb.py <searx/engines/mongodb.py>`


.. automodule:: searx.engines.mongodb
  :members:

