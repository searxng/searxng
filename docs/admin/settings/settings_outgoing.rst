.. _settings outgoing:

=============
``outgoing:``
=============

Communication with search engines.

.. code:: yaml

   outgoing:

     # Suffix to the user-agent SearXNG uses to send requests to others engines.
     useragent_suffix: ""
     # Default timeout in seconds, can be overridden individually by the engines.
     request_timeout: 3.0
     # The maximum timeout in seconds (cannot be exceeded by the engines).
     max_request_timeout: 0.0
     # Number of retry in case of an HTTP error
     retries: 0
     max_redirects: 30
     # See https://www.python-httpx.org/http2/
     enable_http2: true
     # Resource Limits: https://www.python-httpx.org/advanced/resource-limits/
     # Number of allowable keep-alive connections.
     pool_maxsize: 10
     # Maximum number of allowable connections
     pool_connections: 100
     # Number of seconds to keep a connection in the pool.
     keepalive_expiry: 5.0
     # Allow to specify a path to certificate ($SSL_CERT_FILE, $SSL_CERT_DIR).
     #  verify: ~/.mitmproxy/mitmproxy-ca-cert.cer
     #
     # If you have more than one network interface which can be the source of
     # outgoing search requests.
     #
     #  source_ips: [ ... ]
     #
     # To use proxy mounts
     #  proxies:
     #    all://:
     #      - http://proxy1:8080
     #      - socks5://user:pass@host:port
     #
     # Tor configuration
     using_tor_proxy: false
     # Extra seconds to add in order to account for the time taken by the (tor) proxy
     extra_proxy_timeout: 0


``useragent_suffix``:
  Suffix to the user-agent SearXNG uses to send requests to others engines.  If an
  engine wish to block you, a contact info here may be useful to avoid that.

``request_timeout``:
  Global timeout of the requests made to others engines in seconds.  A bigger
  timeout will allow to wait for answers from slow engines, but in consequence
  will slow SearXNG reactivity (the result page may take the time specified in the
  timeout to load).  Can be override by ``timeout`` in the :ref:`settings engines`.

``max_request_timeout``:
  The maximum timeout in seconds (cannot be exceeded by the engines).

``retries``:
  Number of retry in case of an HTTP error.  On each retry, SearXNG uses an
  different proxy and source ip.

``max_redirects``:
  30 by default. Maximum redirect before it is an error.

.. _HTTP/2: https://www.python-httpx.org/http2/

``enable_http2``:
  Enable by default. Set to ``false`` to disable `HTTP/2`_.

.. _Resource Limits: https://www.python-httpx.org/advanced/resource-limits/

``pool_maxsize``:
  Number of allowable keep-alive connections, or ``null`` to always allow.  The
  default is 10.  See ``max_keepalive_connections`` in the `Resource Limits`_.

``pool_connections``:
  Maximum number of allowable connections, or ``null`` for no limits.  The
  default is 100.  See ``max_connections`` in the `Resource Limits`_.

``keepalive_expiry``:
  Number of seconds to keep a connection in the pool.  By default 5.0 seconds.
  See ``keepalive_expiry`` in the `Resource Limits`_.

.. _httpx verification defaults: https://www.python-httpx.org/advanced/#changing-the-verification-defaults
.. _httpx ssl configuration: https://www.python-httpx.org/compatibility/#ssl-configuration

``verify``: ``$SSL_CERT_FILE``, ``$SSL_CERT_DIR``
  Allow to specify a path to certificate. See `httpx verification defaults`_.
  In addition to ``verify``, SearXNG supports the ``$SSL_CERT_FILE`` (for a
  file) and ``$SSL_CERT_DIR`` (for a directory) OpenSSL variables, see `httpx
  ssl configuration`_.

``source_ips``:
  If you use multiple network interfaces, define from which IP the requests must
  be made. Example:

  * ``0.0.0.0`` any local IPv4 address.
  * ``::`` any local IPv6 address.
  * ``192.168.0.1``
  * ``[ 192.168.0.1, 192.168.0.2 ]`` these two specific IP addresses
  * ``fe80::60a2:1691:e5a2:ee1f``
  * ``fe80::60a2:1691:e5a2:ee1f/126`` all IP addresses in this network.
  * ``[ 192.168.0.1, fe80::/126 ]``

.. _proxy mounts: https://www.python-httpx.org/advanced/proxies/#http-proxies
.. _SOCKS: https://www.python-httpx.org/advanced/proxies/#socks
.. _all_proxy: https://www.python-httpx.org/environment_variables/#http_proxy-https_proxy-all_proxy
.. _python request proxies: https://3.python-requests.org/user/advanced/#proxies
.. _python request SOCKS: https://3.python-requests.org/user/advanced/#socks

``proxies``:
  Define one or more `proxy mounts`_ you wish to use (`all_proxy`_, `python
  request proxies`_).  SOCKS_ proxies are also supported (`python request
  SOCKS`_).

  If there are more than one proxy for one protocol (http, https), requests to
  the engines are distributed in a round-robin fashion.

``using_tor_proxy``:
  Using tor proxy (``true``) or not (``false``) for all engines.  The default is
  ``false`` and can be overwritten in the :ref:`settings engines`

``extra_proxy_timeout``:
  Extra seconds to add in order to account for the time taken by the (tor) proxy.
