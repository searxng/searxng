.. _settings redis:

==========
``redis:``
==========

.. _Redis.from_url(url): https://redis-py.readthedocs.io/en/stable/connections.html#redis.client.Redis.from_url

A redis DB can be connected by an URL, in :py:obj:`searx.redisdb` you
will find a description to test your redis connection in SerXNG.  When using
sockets, don't forget to check the access rights on the socket::

  ls -la /usr/local/searxng-redis/run/redis.sock
  srwxrwx--- 1 searxng-redis searxng-redis ... /usr/local/searxng-redis/run/redis.sock

In this example read/write access is given to the *searxng-redis* group.  To get
access rights to redis instance (the socket), your SearXNG (or even your
developer) account needs to be added to the *searxng-redis* group.

``url`` : ``$SEARXNG_REDIS_URL``
  URL to connect redis database, see `Redis.from_url(url)`_ & :ref:`redis db`::

    redis://[[username]:[password]]@localhost:6379/0
    rediss://[[username]:[password]]@localhost:6379/0
    unix://[[username]:[password]]@/path/to/socket.sock?db=0

.. admonition:: Tip for developers

   To set up a local redis instance, first set the socket path of the Redis DB
   in your YAML setting:

   .. code:: yaml

      redis:
        url: unix:///usr/local/searxng-redis/run/redis.sock?db=0

   Then use the following commands to install the redis instance ::

     $ ./manage redis.build
     $ sudo -H ./manage redis.install
     $ sudo -H ./manage redis.addgrp "${USER}"
     # don't forget to logout & login to get member of group

