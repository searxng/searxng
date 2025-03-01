.. _favicons:

========
Favicons
========

.. sidebar:: warning

   Don't activate the favicons before reading the documentation.

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

Activating the favicons in SearXNG is very easy, but this **generates a
significantly higher load** in the client/server communication and increases
resources needed on the server.

To mitigate these disadvantages, various methods have been implemented,
including a *cache*.  The cache must be parameterized according to your own
requirements and maintained regularly.

To activate favicons in SearXNG's result list, set a default
``favicon_resolver`` in the :ref:`search <settings search>` settings:

.. code:: yaml

   search:
     favicon_resolver: "duckduckgo"

By default and without any extensions, SearXNG serves these resolvers:

- ``duckduckgo``
- ``allesedv``
- ``google``
- ``yandex``

With the above setting favicons are displayed, the user has the option to
deactivate this feature in his settings.  If the user is to have the option of
selecting from several *resolvers*, a further setting is required / but this
setting will be discussed :ref:`later <register resolvers>` in this article,
first we have to setup the favicons cache.

Infrastructure
==============

The infrastructure for providing the favicons essentially consists of three
parts:

- :py:obj:`Favicons-Proxy <.favicons.proxy>` (aka *proxy*)
- :py:obj:`Favicons-Resolvers <.favicons.resolvers>` (aka *resolver*)
- :py:obj:`Favicons-Cache <.favicons.cache>` (aka *cache*)

To protect the privacy of users, the favicons are provided via a *proxy*.  This
*proxy* is automatically activated with the above activation of a *resolver*.
Additional requests are required to provide the favicons: firstly, the *proxy*
must process the incoming requests and secondly, the *resolver* must make
outgoing requests to obtain the favicons from external sources.

A *cache* has been developed to massively reduce both, incoming and outgoing
requests.  This *cache* is also activated automatically with the above
activation of a *resolver*.  In its defaults, however, the *cache* is minimal
and not well suitable for a production environment!

.. _favicon cache setup:

Setting up the cache
====================

To parameterize the *cache* and more settings of the favicons infrastructure, a
TOML_ configuration is created in the file ``/etc/searxng/favicons.toml``.

.. code:: toml

   [favicons]

   cfg_schema = 1   # config's schema version no.

   [favicons.cache]

   db_url = "/var/cache/searxng/faviconcache.db"  # default: "/tmp/faviconcache.db"
   LIMIT_TOTAL_BYTES = 2147483648                 # 2 GB / default: 50 MB
   # HOLD_TIME = 5184000                            # 60 days / default: 30 days
   # BLOB_MAX_BYTES = 40960                         # 40 KB / default 20 KB
   # MAINTENANCE_MODE = "off"                       # default: "auto"
   # MAINTENANCE_PERIOD = 600                       # 10min / default: 1h

:py:obj:`cfg_schema <.FaviconConfig.cfg_schema>`:
  Is required to trigger any processes required for future upgrades / don't
  change it.

:py:obj:`cache.db_url <.FaviconCacheConfig.db_url>`:
  The path to the (SQLite_) database file.  The default path is in the `/tmp`_
  folder, which is deleted on every reboot and is therefore unsuitable for a
  production environment.  The FHS_ provides the folder `/var/cache`_ for the
  cache of applications, so a suitable storage location of SearXNG's caches is
  folder ``/var/cache/searxng``.

  In a standard installation (compare :ref:`create searxng user`), the folder
  must be created and the user under which the SearXNG process is running must
  be given write permission to this folder.

  .. code:: bash

     $ sudo mkdir /var/cache/searxng
     $ sudo chown root:searxng /var/cache/searxng/
     $ sudo chmod g+w /var/cache/searxng/

  In container systems, a volume should be mounted for this folder.  Check
  whether the process in the container has read/write access to the mounted
  folder.

:py:obj:`cache.LIMIT_TOTAL_BYTES <.FaviconCacheConfig.LIMIT_TOTAL_BYTES>`:
  Maximum of bytes stored in the cache of all blobs.  The limit is only reached
  at each maintenance interval after which the oldest BLOBs are deleted; the
  limit is exceeded during the maintenance period.

  .. attention::

     If the maintenance period is too long or maintenance is switched
     off completely, the cache grows uncontrollably.

SearXNG hosters can change other parameters of the cache as required:

- :py:obj:`cache.HOLD_TIME <.FaviconCacheConfig.HOLD_TIME>`
- :py:obj:`cache.BLOB_MAX_BYTES <.FaviconCacheConfig.BLOB_MAX_BYTES>`


Maintenance of the cache
------------------------

Regular maintenance of the cache is required!  By default, regular maintenance
is triggered automatically as part of the client requests:

- :py:obj:`cache.MAINTENANCE_MODE <.FaviconCacheConfig.MAINTENANCE_MODE>` (default ``auto``)
- :py:obj:`cache.MAINTENANCE_PERIOD <.FaviconCacheConfig.MAINTENANCE_PERIOD>` (default ``6000`` / 1h)

As an alternative to maintenance as part of the client request process, it is
also possible to carry out maintenance using an external process. For example,
by creating a :man:`crontab` entry for maintenance:

.. code:: bash

   $ python -m searx.favicons cache maintenance

The following command can be used to display the state of the cache:

.. code:: bash

   $ python -m searx.favicons cache state


.. _favicon proxy setup:

Proxy configuration
===================

Most of the options of the :py:obj:`Favicons-Proxy <.favicons.proxy>` are
already set sensibly with settings from the :ref:`settings.yml <searxng
settings.yml>` and should not normally be adjusted.

.. code:: toml

   [favicons.proxy]

   max_age = 5184000             # 60 days / default: 7 days (604800 sec)


:py:obj:`max_age <.FaviconProxyConfig.max_age>`:
  The `HTTP Cache-Control max-age`_ response directive indicates that the
  response remains fresh until N seconds after the response is generated.  This
  setting therefore determines how long a favicon remains in the client's cache.
  As a rule, in the favicons infrastructure of SearXNG's this setting only
  affects favicons whose byte size exceeds :ref:`BLOB_MAX_BYTES <favicon cache
  setup>` (the other favicons that are already in the cache are embedded as
  `data URL`_ in the :py:obj:`generated HTML <.favicons.proxy.favicon_url>`,
  which can greatly reduce the number of additional requests).

.. _register resolvers:

Register resolvers
------------------

A :py:obj:`resolver <.favicon.resolvers>` is a function that obtains the favicon
from an external source.  The resolver functions available to the user are
registered with their fully qualified name (FQN_) in a ``resolver_map``.

If no ``resolver_map`` is defined in the ``favicon.toml``, the favicon
infrastructure of SearXNG generates this ``resolver_map`` automatically
depending on the ``settings.yml``.  SearXNG would automatically generate the
following TOML configuration from the following YAML configuration:

.. code:: yaml

   search:
     favicon_resolver: "duckduckgo"

.. code:: toml

   [favicons.proxy.resolver_map]

   "duckduckgo" = "searx.favicons.resolvers.duckduckgo"

If this automatism is not desired, then (and only then) a separate
``resolver_map`` must be created.  For example, to give the user two resolvers to
choose from, the following configuration could be used:

.. code:: toml

   [favicons.proxy.resolver_map]

   "duckduckgo" = "searx.favicons.resolvers.duckduckgo"
   "allesedv" = "searx.favicons.resolvers.allesedv"
   # "google" = "searx.favicons.resolvers.google"
   # "yandex" = "searx.favicons.resolvers.yandex"

.. note::

   With each resolver, the resource requirement increases significantly.

The number of resolvers increases:

- the number of incoming/outgoing requests and
- the number of favicons to be stored in the cache.

In the following we list the resolvers available in the core of SearXNG, but via
the FQN_ it is also possible to implement your own resolvers and integrate them
into the *proxy*:

- :py:obj:`searx.favicons.resolvers.duckduckgo`
- :py:obj:`searx.favicons.resolvers.allesedv`
- :py:obj:`searx.favicons.resolvers.google`
- :py:obj:`searx.favicons.resolvers.yandex`



.. _SQLite:
   https://www.sqlite.org/
.. _FHS:
   https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html
.. _`/var/cache`:
   https://refspecs.linuxfoundation.org/FHS_3.0/fhs/ch05s05.html
.. _`/tmp`:
   https://refspecs.linuxfoundation.org/FHS_3.0/fhs/ch03s18.html
.. _TOML:
    https://toml.io/en/
.. _HTTP Cache-Control max-age:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#response_directives
.. _data URL:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs
.. _FQN: https://en.wikipedia.org/wiki/Fully_qualified_name

