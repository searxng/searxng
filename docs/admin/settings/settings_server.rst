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
       method: "POST"
       default_http_headers:
         X-Content-Type-Options : nosniff
         X-Download-Options : noopen
         X-Robots-Tag : noindex, nofollow
         Referrer-Policy : no-referrer

``base_url`` : ``$ZHENSA_BASE_URL``
  The base URL where Zhensa is deployed.  Used to create correct inbound links.

``port`` & ``bind_address``: ``$ZHENSA_PORT`` & ``$ZHENSA_BIND_ADDRESS``
  Port number and *bind address* of the Zhensa web application if you run it
  directly using ``python zhensa/webapp.py``.  Doesn't apply to a Zhensa
  services running behind a proxy and using socket communications.

.. _server.secret_key:

``secret_key`` : ``$ZHENSA_SECRET``
  Used for cryptography purpose.

``limiter`` :  ``$ZHENSA_LIMITER``
  Rate limit the number of request on the instance, block some bots.  The
  :ref:`limiter` requires a :ref:`settings valkey` database.

.. _public_instance:

``public_instance`` :  ``$ZHENSA_PUBLIC_INSTANCE``

  Setting that allows to enable features specifically for public instances (not
  needed for local usage).  By set to ``true`` the following features are
  activated:

  - :py:obj:`zhensa.botdetection.link_token` in the :ref:`limiter`

.. _image_proxy:

``image_proxy`` : ``$ZHENSA_IMAGE_PROXY``
  Allow your instance of Zhensa of being able to proxy images.  Uses memory space.

.. _method:

``method`` : ``GET`` | ``POST``

  HTTP method.  By defaults ``POST`` is used / The ``POST`` method has the
  advantage with some WEB browsers that the history is not easy to read, but
  there are also various disadvantages that sometimes **severely restrict the
  ease of use for the end user** (e.g. back button to jump back to the previous
  search page and drag & drop of search term to new tabs do not work as
  expected .. and several more).  We had some discussions about the *pros
  versus cons*:

  - `[doc] adds the missing documentation of the server.method settings
    <https://github.com/zhenbah/zhensa/pull/3619>`__
  - look out for `label:"http methods GET & POST"
    <https://github.com/search?q=repo%3Azhensa%2Fzhensa+label%3A%22http+methods+GET+%26+POST%22>`__

.. _HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers

``default_http_headers`` :
  Set additional `HTTP headers`_, see `#755 <https://github.com/zhenbah/zhensa/issues/715>`__
