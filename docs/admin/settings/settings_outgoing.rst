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
     pool_connections: 100      # Maximum number of concurrent connections (default: 100)
     enable_http2: true         # Enables the use of HTTP2
     # uncomment below section if you want to use a custom server certificate
     #  verify: ~/.mitmproxy/mitmproxy-ca-cert.cer
     #
     # uncomment below section if you want to use a proxy
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
  timeout to load).  Can be override by ``timeout`` in the :ref:`settings engines`.

``useragent_suffix`` :
  Suffix to add when an engine's User-Agent is set via searxng_useragent().
  Contact info here may be useful to avoid an engine blocking you.

.. _Pool limit configuration: https://curl-cffi.readthedocs.io/en/latest/api.html#sessions

``pool_connections`` :
  Maximum number of concurrent connections.  The default is 100.
  See ``max_clients`` `Pool limit configuration`_.

.. _curl_cffi proxies: https://curl-cffi.readthedocs.io/en/latest/quick_start.html

``proxies`` :
  Define one or more proxies you wish to use, see `curl_cffi proxies`_.
  If there are more than one proxy for one protocol (http, https),
  requests to the engines are distributed in a round-robin fashion.

  HTTP, HTTPS, SOCKS4, SOCKS5 and SOCKS5h proxies are supported
  (``http://``, ``https://``, ``socks4://``, ``socks5://``, ``socks5h://``). You should
  use ``socks5h://`` when using Tor so hostnames are resolved by the proxy.

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
  Enable by default (HTTP/2).  Set to ``false`` to force HTTP/1.1.
  HTTP/3 is opt-in per engine (``enable_http3``).

``verify``: : ``$SSL_CERT_FILE``, ``$SSL_CERT_DIR``
  HTTPS verification uses the OS's trust store by default.
  Set a path to use a custom CA file.

  In addition to ``verify``, SearXNG supports the ``$SSL_CERT_FILE`` (for a file) and
  ``$SSL_CERT_DIR`` (for a directory) OpenSSL variables.

``max_redirects`` :
  30 by default. Maximum redirect before it is an error.

``using_tor_proxy`` :
  Using tor proxy (``true``) or not (``false``) for all engines.  The default is
  ``false`` and can be overwritten in the :ref:`settings engines`


