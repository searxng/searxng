.. _searxng.search:

======
Search
======

.. autoclass:: searxng.search.EngineRef
  :members:

.. autoclass:: searxng.search.SearchQuery
  :members:

.. autoclass:: searxng.search.Search

  .. attribute:: search_query
    :type: searxng.search.SearchQuery

  .. attribute:: result_container
    :type: searxng.results.ResultContainer

  .. automethod:: search() -> searxng.results.ResultContainer

.. autoclass:: searxng.search.SearchWithPlugins
  :members:

  .. attribute:: search_query
    :type: searxng.search.SearchQuery

  .. attribute:: result_container
    :type: searxng.results.ResultContainer

  .. attribute:: ordered_plugin_list
    :type: typing.List

  .. attribute:: request
    :type: flask.request

  .. automethod:: search() -> searxng.results.ResultContainer
