.. _settings server:

===========
``server:``
===========

.. code:: yaml

   server:
       base_url: http://example.org/location  # change this!
       port: 8888
       bind_address: "127.0.0.1"
       secret_key: "ultrasecretkey"           # change this!
       limiter: false
       public_instance: false
       image_proxy: false
       default_http_headers:
         X-Content-Type-Options : nosniff
         X-Download-Options : noopen
         X-Robots-Tag : noindex, nofollow
         Referrer-Policy : no-referrer
       enable_tls: false
       certificate_path: "certs/searxng.crt"
       certificate_key_path: "certs/searxng.key"

``base_url`` : ``$SEARXNG_URL``
  The base URL where SearXNG is deployed.  Used to create correct inbound links.

``port`` & ``bind_address``: ``$SEARXNG_PORT`` & ``$SEARXNG_BIND_ADDRESS``
  Port number and *bind address* of the SearXNG web application if you run it
  directly using ``python searx/webapp.py``.  Doesn't apply to a SearXNG
  services running behind a proxy and using socket communications.

``secret_key`` : ``$SEARXNG_SECRET``
  Used for cryptography purpose.

``limiter`` :  ``$SEARXNG_LIMITER``
  Rate limit the number of request on the instance, block some bots.  The
  :ref:`limiter` requires a :ref:`settings redis` database.

.. _public_instance:

``public_instance`` :  ``$SEARXNG_PUBLIC_INSTANCE``

  Setting that allows to enable features specifically for public instances (not
  needed for local usage).  By set to ``true`` the following features are
  activated:

  - :py:obj:`searx.botdetection.link_token` in the :ref:`limiter`

.. _image_proxy:

``image_proxy`` : ``$SEARXNG_IMAGE_PROXY``
  Allow your instance of SearXNG of being able to proxy images.  Uses memory space.

.. _HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers

``default_http_headers`` :
  Set additional HTTP headers, see `#755 <https://github.com/searx/searx/issues/715>`__

``enable_tls`` :
  Enables TLS for the SearXNG flask application. Used to encrypt traffic between 
  the reverse proxy and uWSGI server that hosts the SearXNG flask application.

``certificate_path`` :
  This is the path (relative to /etc/searxng) to the SearXNG certificate. It is used 
  by the SearXNG flask application if enable_tls is set to true.

``certificate_key_path`` :
  This is the path (relative to /etc/searxng) to the key used to create the 
  SearXNG certificate. It is used by the SearXNG flask application if enable_tls is 
  set to true.