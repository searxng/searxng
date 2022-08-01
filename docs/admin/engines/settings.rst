.. _settings.yml:

================
``settings.yml``
================

This page describe the options possibilities of the :origin:`searx/settings.yml`
file.

.. sidebar:: Further reading ..

   - :ref:`use_default_settings.yml`
   - :ref:`search API`

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

.. _settings location:

settings.yml location
=====================

The initial ``settings.yml`` we be load from these locations:

1. the full path specified in the ``SEARXNG_SETTINGS_PATH`` environment variable.
2. ``/etc/searxng/settings.yml``

If these files don't exist (or are empty or can't be read), SearXNG uses the
:origin:`searx/settings.yml` file.  Read :ref:`settings use_default_settings` to
see how you can simplify your *user defined* ``settings.yml``.


.. _settings global:

Global Settings
===============

.. _settings brand:

``brand:``
----------

.. code:: yaml

   brand:
     issue_url: https://github.com/searxng/searxng/issues
     docs_url: https://docs.searxng.org
     public_instances: https://searx.space
     wiki_url: https://github.com/searxng/searxng/wiki

``issue_url`` :
  If you host your own issue tracker change this URL.

``docs_url`` :
  If you host your own documentation change this URL.

``public_instances`` :
  If you host your own https://searx.space change this URL.

``wiki_url`` :
  Link to your wiki (or ``false``)

.. _settings general:

``general:``
------------

.. code:: yaml

   general:
     debug: false
     instance_name:  "SearXNG"
     privacypolicy_url: false
     donation_url: https://docs.searxng.org/donate.html
     contact_url: false
     enable_metrics: true

``debug`` : ``$SEARXNG_DEBUG``
  Allow a more detailed log if you run SearXNG directly. Display *detailed* error
  messages in the browser too, so this must be deactivated in production.

``donation_url`` :
  At default the donation link points to the `SearXNG project
  <https://docs.searxng.org/donate.html>`_.  Set value to ``true`` to use your
  own donation page written in the :ref:`searx/info/en/donate.md
  <searx.infopage>` and use ``false`` to disable the donation link altogether.

``privacypolicy_url``:
  Link to privacy policy.

``contact_url``:
  Contact ``mailto:`` address or WEB form.

``enable_metrics``:
  Enabled by default. Record various anonymous metrics availabled at ``/stats``,
  ``/stats/errors`` and ``/preferences``.

.. _settings search:

``search:``
-----------

.. code:: yaml

   search:
     safe_search: 0
     autocomplete: ""
     default_lang: ""
     ban_time_on_fail: 5
     max_ban_time_on_fail: 120
     formats:
       - html

``safe_search``:
  Filter results.

  - ``0``: None
  - ``1``: Moderate
  - ``2``: Strict

``autocomplete``:
  Existing autocomplete backends, leave blank to turn it off.

  - ``dbpedia``
  - ``duckduckgo``
  - ``google``
  - ``startpage``
  - ``swisscows``
  - ``qwant``
  - ``wikipedia``

``default_lang``:
  Default search language - leave blank to detect from browser information or
  use codes from :origin:`searx/languages.py`.

``languages``:
  List of available languages - leave unset to use all codes from
  :origin:`searx/languages.py`.  Otherwise list codes of available languages.
  The ``all`` value is shown as the ``Default language`` in the user interface
  (in most cases, it is meant to send the query without a language parameter ;
  in some cases, it means the English language) Example:

  .. code:: yaml

     languages:
       - all
       - en
       - en-US
       - de
       - it-IT
       - fr
       - fr-BE

``ban_time_on_fail``:
  Ban time in seconds after engine errors.

``max_ban_time_on_fail``:
  Max ban time in seconds after engine errors.

``formats``:
  Result formats available from web, remove format to deny access (use lower
  case).

  - ``html``
  - ``csv``
  - ``json``
  - ``rss``

.. _settings server:

``server:``
-----------

.. code:: yaml

   server:
       base_url: false                # set custom base_url (or false)
       port: 8888
       bind_address: "127.0.0.1"      # address to listen on
       secret_key: "ultrasecretkey"   # change this!
       limiter: false
       image_proxy: false             # proxying image results through SearXNG
       default_http_headers:
         X-Content-Type-Options : nosniff
         X-XSS-Protection : 1; mode=block
         X-Download-Options : noopen
         X-Robots-Tag : noindex, nofollow
         Referrer-Policy : no-referrer

.. sidebar::  buildenv

   Changing a value tagged by :ref:`buildenv <make buildenv>`, needs to
   rebuild instance's environment :ref:`utils/brand.env <make buildenv>`.

``base_url`` : :ref:`buildenv SEARXNG_URL <make buildenv>`
  The base URL where SearXNG is deployed.  Used to create correct inbound links.
  If you change the value, don't forget to rebuild instance's environment
  (:ref:`utils/brand.env <make buildenv>`)

``port`` & ``bind_address``: :ref:`buildenv SEARXNG_PORT & SEARXNG_BIND_ADDRESS <make buildenv>`
  Port number and *bind address* of the SearXNG web application if you run it
  directly using ``python searx/webapp.py``.  Doesn't apply to SearXNG running on
  Apache or Nginx.

``secret_key`` : ``$SEARXNG_SECRET``
  Used for cryptography purpose.

.. _limiter:

``limiter`` :
  Rate limit the number of request on the instance, block some bots.  The
  :ref:`limiter plugin` requires a :ref:`settings redis` database.

.. _image_proxy:

``image_proxy`` :
  Allow your instance of SearXNG of being able to proxy images.  Uses memory space.

.. _HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers

``default_http_headers`` :
  Set additional HTTP headers, see `#755 <https://github.com/searx/searx/issues/715>`__


.. _settings ui:

``ui:``
-------

.. _cache busting:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#caching_static_assets_with_cache_busting

.. code:: yaml

   ui:
     static_use_hash: false
     default_locale: ""
     query_in_title: false
     infinite_scroll: false
     center_alignment: false
     default_theme: simple
     theme_args:
       simple_style: auto

.. _static_use_hash:

``static_use_hash`` :
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
  (:origin:`min-width: @tablet <searx/static/themes/simple/src/less/definitions.less>`)

``default_theme`` :
  Name of the theme you want to use by default on your SearXNG instance.

``theme_args.simple_style``:
  Style of simple theme: ``auto``, ``light``, ``dark``

``results_on_new_tab``:
  Open result links in a new tab by default.


.. _settings redis:

``redis:``
----------

.. _Redis.from_url(url): https://redis-py.readthedocs.io/en/stable/connections.html#redis.client.Redis.from_url

A redis DB can be connected by an URL, in :py:obj:`searx.shared.redisdb` you
will find a description to test your redis connection in SerXNG.  When using
sockets, don't forget to check the access rights on the socket::

  ls -la /usr/local/searxng-redis/run/redis.sock
  srwxrwx--- 1 searxng-redis searxng-redis ... /usr/local/searxng-redis/run/redis.sock

In this example read/write access is given to the *searxng-redis* group.  To get
access rights to redis instance (the socket), your SearXNG (or even your
developer) account needs to be added to the *searxng-redis* group.

``url``
  URL to connect redis database, see `Redis.from_url(url)`_ & :ref:`redis db`::

    redis://[[username]:[password]]@localhost:6379/0
    rediss://[[username]:[password]]@localhost:6379/0
    unix://[[username]:[password]]@/path/to/socket.sock?db=0

.. admonition:: Tip for developers

   To set up a local redis instance using sockets simply use::

     $ ./manage redis.build
     $ sudo -H ./manage redis.install
     $ sudo -H ./manage redis.addgrp "${USER}"
     # don't forget to logout & login to get member of group

   The YAML setting for such a redis instance is:

   .. code:: yaml

      redis:
        url: unix:///usr/local/searxng-redis/run/redis.sock?db=0


.. _settings outgoing:

``outgoing:``
-------------

Communication with search engines.

.. code:: yaml

   outgoing:
     request_timeout: 2.0       # default timeout in seconds, can be override by engine
     max_request_timeout: 10.0  # the maximum timeout in seconds
     useragent_suffix: ""       # informations like an email address to the administrator
     pool_connections: 100      # Maximum number of allowable connections, or null
                                # for no limits. The default is 100.
     pool_maxsize: 10           # Number of allowable keep-alive connections, or null
                                # to always allow. The default is 10.
     enable_http2: true         # See https://www.python-httpx.org/http2/
     # uncomment below section if you want to use a proxy
     # proxies:
     #   all://:
     #     - http://proxy1:8080
     #     - http://proxy2:8080
     # uncomment below section only if you have more than one network interface
     # which can be the source of outgoing search requests
     # source_ips:
     #   - 1.1.1.1
     #   - 1.1.1.2
     #   - fe80::/126


``request_timeout`` :
  Global timeout of the requests made to others engines in seconds.  A bigger
  timeout will allow to wait for answers from slow engines, but in consequence
  will slow SearXNG reactivity (the result page may take the time specified in the
  timeout to load). Can be override by :ref:`settings engine`

``useragent_suffix`` :
  Suffix to the user-agent SearXNG uses to send requests to others engines.  If an
  engine wish to block you, a contact info here may be useful to avoid that.

``keepalive_expiry`` :
  Number of seconds to keep a connection in the pool. By default 5.0 seconds.

.. _httpx proxies: https://www.python-httpx.org/advanced/#http-proxying

``proxies`` :
  Define one or more proxies you wish to use, see `httpx proxies`_.
  If there are more than one proxy for one protocol (http, https),
  requests to the engines are distributed in a round-robin fashion.

``source_ips`` :
  If you use multiple network interfaces, define from which IP the requests must
  be made. Example:

  * ``0.0.0.0`` any local IPv4 address.
  * ``::`` any local IPv6 address.
  * ``192.168.0.1``
  * ``[ 192.168.0.1, 192.168.0.2 ]`` these two specific IP addresses
  * ``fe80::60a2:1691:e5a2:ee1f``
  * ``fe80::60a2:1691:e5a2:ee1f/126`` all IP addresses in this network.
  * ``[ 192.168.0.1, fe80::/126 ]``

``retries`` :
  Number of retry in case of an HTTP error.  On each retry, SearXNG uses an
  different proxy and source ip.

``retry_on_http_error`` :
  Retry request on some HTTP status code.

  Example:

  * ``true`` : on HTTP status code between 400 and 599.
  * ``403`` : on HTTP status code 403.
  * ``[403, 429]``: on HTTP status code 403 and 429.

``enable_http2`` :
  Enable by default. Set to ``false`` to disable HTTP/2.

``max_redirects`` :
  30 by default. Maximum redirect before it is an error.

``categories_as_tabs:``
-----------------------

A list of the categories that are displayed as tabs in the user interface.
Categories not listed here can still be searched with the :ref:`search-syntax`.

.. code-block:: yaml

  categories_as_tabs:
    general:
    images:
    videos:
    news:
    map:
    music:
    it:
    science:
    files:
    social media:

.. _settings engine:

Engine settings
===============

.. sidebar:: Further reading ..

   - :ref:`configured engines`
   - :ref:`engines-dev`

In the code example below a *full fledged* example of a YAML setup from a dummy
engine is shown.  Most of the options have a default value or even are optional.

.. code:: yaml

   - name: example engine
     engine: example
     shortcut: demo
     base_url: 'https://{language}.example.com/'
     send_accept_language_header: false
     categories: general
     timeout: 3.0
     api_key: 'apikey'
     disabled: false
     language: en_US
     tokens: [ 'my-secret-token' ]
     weigth: 1
     display_error_messages: true
     about:
        website: https://example.com
        wikidata_id: Q306656
        official_api_documentation: https://example.com/api-doc
        use_official_api: true
        require_api_key: true
        results: HTML
     enable_http: false
     enable_http2: false
     retries: 1
     retry_on_http_error: true # or 403 or [404, 429]
     max_connections: 100
     max_keepalive_connections: 10
     keepalive_expiry: 5.0
     proxies:
       http:
         - http://proxy1:8080
         - http://proxy2:8080
       https:
         - http://proxy1:8080
         - http://proxy2:8080
         - socks5://user:password@proxy3:1080
         - socks5h://user:password@proxy4:1080

``name`` :
  Name that will be used across SearXNG to define this engine.  In settings, on
  the result page...

``engine`` :
  Name of the python file used to handle requests and responses to and from this
  search engine.

``shortcut`` :
  Code used to execute bang requests (in this case using ``!bi``)

``base_url`` : optional
  Part of the URL that should be stable across every request.  Can be useful to
  use multiple sites using only one engine, or updating the site URL without
  touching at the code.

``send_accept_language_header`` :
  Several engines that support languages (or regions) deal with the HTTP header
  ``Accept-Language`` to build a response that fits to the locale.  When this
  option is activated, the language (locale) that is selected by the user is used
  to build and send a ``Accept-Language`` header in the request to the origin
  search engine.

``categories`` : optional
  Define in which categories this engine will be active.  Most of the time, it is
  defined in the code of the engine, but in a few cases it is useful, like when
  describing multiple search engine using the same code.

``timeout`` : optional
  Timeout of the search with the current search engine.  **Be careful, it will
  modify the global timeout of SearXNG.**

``api_key`` : optional
  In a few cases, using an API needs the use of a secret key.  How to obtain them
  is described in the file.

``disabled`` : optional
  To disable by default the engine, but not deleting it.  It will allow the user
  to manually activate it in the settings.

``language`` : optional
  If you want to use another language for a specific engine, you can define it
  by using the full ISO code of language and country, like ``fr_FR``, ``en_US``,
  ``de_DE``.

``tokens`` : optional
  A list of secret tokens to make this engine *private*, more details see
  :ref:`private engines`.

``weigth`` : default ``1``
  Weighting of the results of this engine.

``display_error_messages`` : default ``true``
  When an engine returns an error, the message is displayed on the user interface.

``network`` : optional
  Use the network configuration from another engine.
  In addition, there are two default networks:

  - ``ipv4`` set ``local_addresses`` to ``0.0.0.0`` (use only IPv4 local addresses)
  - ``ipv6`` set ``local_addresses`` to ``::`` (use only IPv6 local addresses)

.. note::

   A few more options are possible, but they are pretty specific to some
   engines, and so won't be described here.


Example: Multilingual Search
----------------------------

SearXNG does not support true multilingual search.  You have to use the language
prefix in your search query when searching in a different language.

But there is a workaround: By adding a new search engine with a different
language, SearXNG will search in your default and other language.

Example configuration in settings.yml for a German and English speaker:

.. code-block:: yaml

    search:
        default_lang : "de"
        ...

    engines:
      - name : google english
        engine : google
        language : en
        ...

When searching, the default google engine will return German results and
"google english" will return English results.


.. _settings use_default_settings:

use_default_settings
====================

.. sidebar:: ``use_default_settings: true``

   - :ref:`settings location`
   - :ref:`use_default_settings.yml`
   - :origin:`/etc/searxng/settings.yml <utils/templates/etc/searxng/settings.yml>`

The user defined ``settings.yml`` is loaded from the :ref:`settings location`
and can relied on the default configuration :origin:`searx/settings.yml` using:

 ``use_default_settings: true``

``server:``
  In the following example, the actual settings are the default settings defined
  in :origin:`searx/settings.yml` with the exception of the ``secret_key`` and
  the ``bind_address``:

  .. code-block:: yaml

    use_default_settings: true
    server:
        secret_key: "ultrasecretkey"   # change this!
        bind_address: "0.0.0.0"

``engines:``
  With ``use_default_settings: true``, each settings can be override in a
  similar way, the ``engines`` section is merged according to the engine
  ``name``.  In this example, SearXNG will load all the engine and the arch linux
  wiki engine has a :ref:`token <private engines>`:

  .. code-block:: yaml

    use_default_settings: true
    server:
      secret_key: "ultrasecretkey"   # change this!
    engines:
      - name: arch linux wiki
        tokens: ['$ecretValue']

``engines:`` / ``remove:``
  It is possible to remove some engines from the default settings. The following
  example is similar to the above one, but SearXNG doesn't load the the google
  engine:

  .. code-block:: yaml

    use_default_settings:
      engines:
        remove:
          - google
    server:
      secret_key: "ultrasecretkey"   # change this!
    engines:
      - name: arch linux wiki
        tokens: ['$ecretValue']

``engines:`` / ``keep_only:``
  As an alternative, it is possible to specify the engines to keep. In the
  following example, SearXNG has only two engines:

  .. code-block:: yaml

    use_default_settings:
      engines:
        keep_only:
          - google
          - duckduckgo
    server:
      secret_key: "ultrasecretkey"   # change this!
    engines:
      - name: google
        tokens: ['$ecretValue']
      - name: duckduckgo
        tokens: ['$ecretValue']
