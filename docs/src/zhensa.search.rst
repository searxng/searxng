.. _zhensa.search:

======
Search
======

.. autoclass:: zhensa.search.models.EngineRef
  :members:

.. autoclass:: zhensa.search.models.SearchQuery
  :members:

.. autoclass:: zhensa.search.Search

  .. attribute:: search_query
    :type: zhensa.search.SearchQuery

  .. attribute:: result_container
    :type: zhensa.results.ResultContainer

  .. automethod:: search() -> zhensa.results.ResultContainer

.. autoclass:: zhensa.search.SearchWithPlugins
  :members:

  .. attribute:: search_query
    :type: zhensa.search.SearchQuery

  .. attribute:: result_container
    :type: zhensa.results.ResultContainer

  .. attribute:: ordered_plugin_list
    :type: typing.List

  .. attribute:: request
    :type: flask.request

  .. automethod:: search() -> zhensa.results.ResultContainer
