.. _settings outgoing:

=============
``outgoing:``
=============

Communication with search engines.

.. code:: yaml

   outgoing:
     request_timeout: 2.0       # default timeout in seconds, can be override by engine
     max_request_timeout: 10.0  # the maximum timeout in seconds
     useragent_suffix: ""       # information like an email address to the administrator
     pool_connections: 100      # Maximum number of allowable connections, or null
                                # for no limits. The default is 100.
     pool_maxsize: 10           # Number of allowable keep-alive connections, or null
                                # to always allow. The default is 10.
     enable_http2: true         # See https://www.python-httpx.org/http2/
     # uncomment below section if you want to use a custom server certificate
     # see https://www.python-httpx.org/advanced/#changing-the-verification-defaults
     # and https://www.python-httpx.org/compatibility/#ssl-configuration
     #  verify: ~/.mitmproxy/mitmproxy-ca-cert.cer
     #
     # uncomment below section if you want to use a proxyq see: SOCKS proxies
     #   https://2.python-requests.org/en/latest/user/advanced/#proxies
     # are also supported: see
     #   https://2.python-requests.org/en/latest/user/advanced/#socks
     #
     #  proxies:
     #    all://:
     #      - http://proxy1:8080
     #      - http://proxy2:8080
     #
     #  using_tor_proxy: true
     #
     # Extra seconds to add in order to account for the time taken by the proxy
     #
     #  extra_proxy_timeout: 10.0
     #

``request_timeout`` :
  Global timeout of the requests made to others engines in seconds.  A bigger
  timeout will allow to wait for answers from slow engines, but in consequence
  will slow SearXNG reactivity (the result page may take the time specified in the
  timeout to load).  Can be override by ``timeout`` in the :ref:`settings engine`.

``useragent_suffix`` :
  Suffix to the user-agent SearXNG uses to send requests to others engines.  If an
  engine wish to block you, a contact info here may be useful to avoid that.

.. _Pool limit configuration: https://www.python-httpx.org/advanced/#pool-limit-configuration

``pool_maxsize``:
  Number of allowable keep-alive connections, or ``null`` to always allow.  The
  default is 10.  See ``max_keepalive_connections`` `Pool limit configuration`_.

``pool_connections`` :
  Maximum number of allowable connections, or ``null`` # for no limits.  The
  default is 100.  See ``max_connections`` `Pool limit configuration`_.

``keepalive_expiry`` :
  Number of seconds to keep a connection in the pool.  By default 5.0 seconds.
  See ``keepalive_expiry`` `Pool limit configuration`_.

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

``enable_http2`` :
  Enable by default. Set to ``false`` to disable HTTP/2.

.. _httpx verification defaults: https://www.python-httpx.org/advanced/#changing-the-verification-defaults
.. _httpx ssl configuration: https://www.python-httpx.org/compatibility/#ssl-configuration

``verify``: : ``$SSL_CERT_FILE``, ``$SSL_CERT_DIR``
  Allow to specify a path to certificate.
  see `httpx verification defaults`_.

  In addition to ``verify``, SearXNG supports the ``$SSL_CERT_FILE`` (for a file) and
  ``$SSL_CERT_DIR`` (for a directory) OpenSSL variables.
  see `httpx ssl configuration`_.

``max_redirects`` :
  30 by default. Maximum redirect before it is an error.

``using_tor_proxy`` :
  Using tor proxy (``true``) or not (``false``) for all engines.  The default is
  ``false`` and can be overwritten in the :ref:`settings engine`


