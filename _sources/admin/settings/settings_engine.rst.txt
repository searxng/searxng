.. _settings engine:

===========
``engine:``
===========

.. sidebar:: Further reading ..

   - :ref:`configured engines`
   - :ref:`engines-dev`

In the code example below a *full fledged* example of a YAML setup from a dummy
engine is shown.  Most of the options have a default value or even are optional.

.. hint::

   A few more options are possible, but they are pretty specific to some
   engines (:ref:`engine implementations`).

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
     weight: 1
     display_error_messages: true
     about:
        website: https://example.com
        wikidata_id: Q306656
        official_api_documentation: https://example.com/api-doc
        use_official_api: true
        require_api_key: true
        results: HTML

     # overwrite values from section 'outgoing:'
     enable_http2: false
     retries: 1
     max_connections: 100
     max_keepalive_connections: 10
     keepalive_expiry: 5.0
     using_tor_proxy: false
     proxies:
       http:
         - http://proxy1:8080
         - http://proxy2:8080
       https:
         - http://proxy1:8080
         - http://proxy2:8080
         - socks5://user:password@proxy3:1080
         - socks5h://user:password@proxy4:1080

     # other network settings
     enable_http: false
     retry_on_http_error: true # or 403 or [404, 429]


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

.. _engine categories:

``categories`` : optional
  Specifies to which categories the engine should be added.  Engines can be
  assigned to multiple categories.

  Categories can be shown as tabs (:ref:`settings categories_as_tabs`) in the
  UI.  A search in a tab (in the UI) will query all engines that are active in
  this tab.  In the preferences page (``/preferences``) -- under *engines* --
  users can select what engine should be active when querying in this tab.

  Alternatively, :ref:`\!bang <search-syntax>` can be used to search all engines
  in a category, regardless of whether they are active or not, or whether they
  are in a tab of the UI or not.  For example, ``!dictionaries`` can be used to
  query all search engines in that category (group).

``timeout`` : optional
  Timeout of the search with the current search engine.  Overwrites
  ``request_timeout`` from :ref:`settings outgoing`.  **Be careful, it will
  modify the global timeout of SearXNG.**

``api_key`` : optional
  In a few cases, using an API needs the use of a secret key.  How to obtain them
  is described in the file.

``disabled`` : optional
  To disable by default the engine, but not deleting it.  It will allow the user
  to manually activate it in the settings.

``inactive``: optional
  Remove the engine from the settings (*disabled & removed*).

``language`` : optional
  If you want to use another language for a specific engine, you can define it
  by using the ISO code of language (and region), like ``fr``, ``en-US``,
  ``de-DE``.

``tokens`` : optional
  A list of secret tokens to make this engine *private*, more details see
  :ref:`private engines`.

``weight`` : default ``1``
  Weighting of the results of this engine.

``display_error_messages`` : default ``true``
  When an engine returns an error, the message is displayed on the user interface.

``network`` : optional
  Use the network configuration from another engine.
  In addition, there are two default networks:

  - ``ipv4`` set ``local_addresses`` to ``0.0.0.0`` (use only IPv4 local addresses)
  - ``ipv6`` set ``local_addresses`` to ``::`` (use only IPv6 local addresses)

``enable_http`` : optional
  Enable HTTP for this engine (by default only HTTPS is enabled).

``retry_on_http_error`` : optional
  Retry request on some HTTP status code.

  Example:

  * ``true`` : on HTTP status code between 400 and 599.
  * ``403`` : on HTTP status code 403.
  * ``[403, 429]``: on HTTP status code 403 and 429.

``proxies`` :
  Overwrites proxy settings from :ref:`settings outgoing`.

``using_tor_proxy`` :
  Using tor proxy (``true``) or not (``false``) for this engine.  The default is
  taken from ``using_tor_proxy`` of the :ref:`settings outgoing`.

.. _Pool limit configuration: https://www.python-httpx.org/advanced/#pool-limit-configuration

``max_keepalive_connection#s`` :
  `Pool limit configuration`_, overwrites value ``pool_maxsize`` from
   :ref:`settings outgoing` for this engine.

``max_connections`` :
  `Pool limit configuration`_, overwrites value ``pool_connections`` from
  :ref:`settings outgoing` for this engine.

``keepalive_expiry`` :
  `Pool limit configuration`_, overwrites value ``keepalive_expiry`` from
  :ref:`settings outgoing` for this engine.


.. _private engines:

Private Engines (``tokens``)
============================

Administrators might find themselves wanting to limit access to some of the
enabled engines on their instances.  It might be because they do not want to
expose some private information through :ref:`offline engines`.  Or they would
rather share engines only with their trusted friends or colleagues.

.. sidebar:: info

   Initial sponsored by `Search and Discovery Fund
   <https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.

To solve this issue the concept of *private engines* exists.

A new option was added to engines named `tokens`.  It expects a list of strings.
If the user making a request presents one of the tokens of an engine, they can
access information about the engine and make search requests.

Example configuration to restrict access to the Arch Linux Wiki engine:

.. code:: yaml

  - name: arch linux wiki
    engine: archlinux
    shortcut: al
    tokens: [ 'my-secret-token' ]

Unless a user has configured the right token, the engine is going to be hidden
from him/her.  It is not going to be included in the list of engines on the
Preferences page and in the output of `/config` REST API call.

Tokens can be added to one's configuration on the Preferences page under "Engine
tokens".  The input expects a comma separated list of strings.

The distribution of the tokens from the administrator to the users is not carved
in stone.  As providing access to such engines implies that the admin knows and
trusts the user, we do not see necessary to come up with a strict process.
Instead, we would like to add guidelines to the documentation of the feature.


Example: Multilingual Search
============================

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

