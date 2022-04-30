.. _search API:

==========
Search API
==========

The search supports both ``GET`` and ``POST``.

Furthermore, two endpoints ``/`` and ``/search`` are available for querying.


``GET /``

``GET /search``

Parameters
==========

.. sidebar:: Further reading ..

   - :ref:`engines-dev`
   - :ref:`settings.yml`
   - :ref:`configured engines`

``q`` : required
  The search query.  This string is passed to external search services.  Thus,
  SearXNG supports syntax of each search service.  For example, ``site:github.com
  SearXNG`` is a valid query for Google.  However, if simply the query above is
  passed to any search engine which does not filter its results based on this
  syntax, you might not get the results you wanted.

  See more at :ref:`search-syntax`

``categories`` : optional
  Comma separated list, specifies the active search categories

``engines`` : optional
  Comma separated list, specifies the active search engines.

``lang`` : default ``all``
  Code of the language.

``pageno`` : default ``1``
  Search page number.

``time_range`` : optional
  [ ``day``, ``month``, ``year`` ]

  Time range of search for engines which support it.  See if an engine supports
  time range search in the preferences page of an instance.

``format`` : optional
  [ ``json``, ``csv``, ``rss`` ]

  Output format of results.

``results_on_new_tab`` : default ``0``
  [ ``0``, ``1`` ]

  Open search results on new tab.

``image_proxy`` : default ``False``
  [  ``True``, ``False`` ]

  Proxy image results through SearXNG.

``autocomplete`` : default *empty*
  [ ``google``, ``dbpedia``, ``duckduckgo``, ``startpage``, ``wikipedia`` ]

  Service which completes words as you type.

``safesearch`` :  default ``None``
  [ ``0``, ``1``, ``None`` ]

  Filter search results of engines which support safe search.  See if an engine
  supports safe search in the preferences page of an instance.

``theme`` : default ``simple``
  [ ``simple`` ]

  Theme of instance.

  Please note, available themes depend on an instance.  It is possible that an
  instance administrator deleted, created or renamed themes on their instance.
  See the available options in the preferences page of the instance.

``enabled_plugins`` : optional
  List of enabled plugins.

  :default: ``HTTPS_rewrite``, ``Self_Informations``,
    ``Search_on_category_select``, ``Tracker_URL_remover``

  :values: ``DOAI_rewrite``, ``HTTPS_rewrite``, ``Infinite_scroll``,
    ``Vim-like_hotkeys``, ``Self_Informations``, ``Tracker_URL_remover``,
    ``Search_on_category_select``, ``Hostname_replace``

``disabled_plugins``: optional
  List of disabled plugins.

  :default: ``DOAI_rewrite``, ``Infinite_scroll``, ``Vim-like_hotkeys``, ``Hostname_replace``
  :values: ``DOAI_rewrite``, ``HTTPS_rewrite``, ``Infinite_scroll``,
    ``Vim-like_hotkeys``, ``Self_Informations``, ``Tracker_URL_remover``,
    ``Search_on_category_select``, ``Hostname_replace``

``enabled_engines`` : optional : *all* :origin:`engines <searx/engines>`
  List of enabled engines.

``disabled_engines`` : optional : *all* :origin:`engines <searx/engines>`
  List of disabled engines.

