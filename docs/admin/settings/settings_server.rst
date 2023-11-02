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
       public_instance: false
       limiter: false
       pass_searxng_org: false
       image_proxy: false
       default_http_headers:
         X-Content-Type-Options : nosniff
         X-Download-Options : noopen
         X-Robots-Tag : noindex, nofollow
         Referrer-Policy : no-referrer

``base_url`` : ``$SEARXNG_URL``
  The base URL where SearXNG is deployed.  Used to create correct inbound links.

``port`` & ``bind_address``: ``$SEARXNG_PORT`` & ``$SEARXNG_BIND_ADDRESS``
  Port number and *bind address* of the SearXNG web application if you run it
  directly using ``python searx/webapp.py``.  Doesn't apply to a SearXNG
  services running behind a proxy and using socket communications.

``secret_key`` : ``$SEARXNG_SECRET``
  Used for cryptography purpose.

.. _public_instance:

``public_instance`` :

  Setting that allows to enable features specifically for public instances (not
  needed for local usage).  By set to ``true`` the following features are
  activated:

  - ``server: limiter`` option :ref:`see below <activate limiter>`
  - ``server: pass_searxng_org`` option :ref:`see below <pass_searxng_org>`
  - :py:obj:`botdetection.link_token` in the :ref:`limiter`

.. _activate limiter:

``limiter`` :
  Rate limit the number of request on the instance, block some bots.  The
  :ref:`limiter` requires a :ref:`settings redis` database.

.. _pass_searxng_org:

``pass_searxng_org`` :
  In the limiter activates the passlist of (hardcoded) IPs of the SearXNG
  organization, e.g. ``check.searx.space``.

.. _image_proxy:

``image_proxy`` :
  Allow your instance of SearXNG of being able to proxy images.  Uses memory space.

.. _HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers

``default_http_headers`` :
  Set additional HTTP headers, see `#755 <https://github.com/searx/searx/issues/715>`__

