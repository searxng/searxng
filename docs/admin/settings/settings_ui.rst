.. _settings ui:

=======
``ui:``
=======

.. _cache busting:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#caching_static_assets_with_cache_busting

.. code:: yaml

   ui:
     static_use_hash: false
     default_locale: ""
     query_in_title: false
     infinite_scroll: false
     center_alignment: false
     cache_url: https://web.archive.org/web/
     default_theme: simple
     theme_args:
       simple_style: auto
     search_on_category_select: true
     hotkeys: default
     url_formatting: pretty

.. _static_use_hash:

``static_use_hash`` : ``$SEARXNG_STATIC_USE_HASH``
  Enables `cache busting`_ of static files.

``default_locale`` :
  SearXNG interface language.  If blank, the locale is detected by using the
  browser language.  If it doesn't work, or you are deploying a language
  specific instance of searx, a locale can be defined using an ISO language
  code, like ``fr``, ``en``, ``de``.

``query_in_title`` :
  When true, the result page's titles contains the query it decreases the
  privacy, since the browser can records the page titles.

``infinite_scroll``:
  When true, automatically loads the next page when scrolling to bottom of the current page.

``center_alignment`` : default ``false``
  When enabled, the results are centered instead of being in the left (or RTL)
  side of the screen.  This setting only affects the *desktop layout*
  (:origin:`min-width: @tablet <client/simple/src/less/definitions.less>`)

.. cache_url:

``cache_url`` : ``https://web.archive.org/web/``
  URL prefix of the internet archive or cache, don't forget trailing slash (if
  needed).  The default is https://web.archive.org/web/ alternatives are:

  - https://webcache.googleusercontent.com/search?q=cache:
  - https://archive.today/

``default_theme`` :
  Name of the theme you want to use by default on your SearXNG instance.

``theme_args.simple_style``:
  Style of simple theme: ``auto``, ``light``, ``dark``, ``black``

``results_on_new_tab``:
  Open result links in a new tab by default.

``search_on_category_select``:
  Perform search immediately if a category selected. Disable to select multiple categories.

``hotkeys``:
  Hotkeys to use in the search interface: ``default``, ``vim`` (Vim-like).

``url_formatting``:
  Formatting type to use for result URLs: ``pretty``, ``full`` or ``host``.
