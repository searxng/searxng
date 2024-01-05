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
  Comma separated list, specifies the active search categories (see
  :ref:`configured engines`)

``engines`` : optional
  Comma separated list, specifies the active search engines (see
  :ref:`configured engines`).

``language`` : default from :ref:`settings search`
  Code of the language.

``pageno`` : default ``1``
  Search page number.

``time_range`` : optional
  [ ``day``, ``month``, ``year`` ]

  Time range of search for engines which support it.  See if an engine supports
  time range search in the preferences page of an instance.

``format`` : optional
  [ ``json``, ``csv``, ``rss`` ]

  Output format of results.  Format needs to be activated in :ref:`settings
  search`.

``results_on_new_tab`` : default ``0``
  [ ``0``, ``1`` ]

  Open search results on new tab.

``image_proxy`` : default from :ref:`settings server`
  [  ``True``, ``False`` ]

  Proxy image results through SearXNG.

``autocomplete`` : default from :ref:`settings search`
  [ ``google``, ``dbpedia``, ``duckduckgo``, ``mwmbl``, ``startpage``,
  ``wikipedia``, ``stract``, ``swisscows``, ``qwant`` ]

  Service which completes words as you type.

``safesearch`` :  default from :ref:`settings search`
  [ ``0``, ``1``, ``2`` ]

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

  :default:
     ``Hash_plugin``, ``Self_Information``,
     ``Tracker_URL_remover``, ``Ahmia_blacklist``

  :values:
     .. enabled by default

     ``Hash_plugin``, ``Self_Information``,
     ``Tracker_URL_remover``, ``Ahmia_blacklist``,

     .. disabled by default

     ``Hostname_replace``, ``Open_Access_DOI_rewrite``,
     ``Vim-like_hotkeys``, ``Tor_check_plugin``

``disabled_plugins``: optional
  List of disabled plugins.

  :default:
     ``Hostname_replace``, ``Open_Access_DOI_rewrite``,
     ``Vim-like_hotkeys``, ``Tor_check_plugin``

  :values:
     see values from ``enabled_plugins``

``enabled_engines`` : optional : *all* :origin:`engines <searx/engines>`
  List of enabled engines.

``disabled_engines`` : optional : *all* :origin:`engines <searx/engines>`
  List of disabled engines.

