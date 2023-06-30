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
       image_proxy: false
       default_http_headers:
         X-Content-Type-Options : nosniff
         X-XSS-Protection : 1; mode=block
         X-Download-Options : noopen
         X-Robots-Tag : noindex, nofollow
         Referrer-Policy : no-referrer


``base_url`` : ``$SEARXNG_URL`` :ref:`buildenv <make buildenv>`
  The base URL where SearXNG is deployed.  Used to create correct inbound links.
  If you change the value, don't forget to rebuild instance's environment
  (:ref:`utils/brand.env <make buildenv>`)

``port`` & ``bind_address``: ``$SEARXNG_PORT`` & ``$SEARXNG_BIND_ADDRESS`` :ref:`buildenv <make buildenv>`
  Port number and *bind address* of the SearXNG web application if you run it
  directly using ``python searx/webapp.py``.  Doesn't apply to a SearXNG
  services running behind a proxy and using socket communications.  If you
  change the value, don't forget to rebuild instance's environment
  (:ref:`utils/brand.env <make buildenv>`)

``secret_key`` : ``$SEARXNG_SECRET``
  Used for cryptography purpose.

.. _limiter:

``limiter`` :
  Rate limit the number of request on the instance, block some bots.  The
  :ref:`limiter src` requires a :ref:`settings redis` database.

.. _image_proxy:

``image_proxy`` :
  Allow your instance of SearXNG of being able to proxy images.  Uses memory space.

.. _HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers

``default_http_headers`` :
  Set additional HTTP headers, see `#755 <https://github.com/searx/searx/issues/715>`__

