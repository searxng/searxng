.. _searx.search:

======
Search
======

.. autoclass:: searx.search.models.EngineRef
  :members:

.. autoclass:: searx.search.models.SearchQuery
  :members:

.. autoclass:: searx.search.Search

  .. attribute:: search_query
    :type: searx.search.SearchQuery

  .. attribute:: result_container
    :type: searx.results.ResultContainer

  .. automethod:: search() -> searx.results.ResultContainer

.. autoclass:: searx.search.SearchWithPlugins
  :members:

  .. attribute:: search_query
    :type: searx.search.SearchQuery

  .. attribute:: result_container
    :type: searx.results.ResultContainer

  .. attribute:: ordered_plugin_list
    :type: typing.List

  .. attribute:: request
    :type: flask.request

  .. automethod:: search() -> searx.results.ResultContainer
