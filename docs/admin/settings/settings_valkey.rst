.. _settings valkey:

==========
``valkey:``
==========

.. _Valkey.from_url(url): https://valkey-py.readthedocs.io/en/stable/connections.html#valkey.Valkey.from_url

A valkey DB can be connected by an URL, in :py:obj:`searx.valkeydb` you
will find a description to test your valkey connection in SearXNG.  When using
sockets, don't forget to check the access rights on the socket::

  ls -la /usr/local/searxng-valkey/run/valkey.sock
  srwxrwx--- 1 searxng-valkey searxng-valkey ... /usr/local/searxng-valkey/run/valkey.sock

In this example read/write access is given to the *searxng-valkey* group.  To get
access rights to valkey instance (the socket), your SearXNG (or even your
developer) account needs to be added to the *searxng-valkey* group.

``url`` : ``$SEARXNG_VALKEY_URL``
  URL to connect valkey database, see `Valkey.from_url(url)`_ & :ref:`valkey db`::

    valkey://[[username]:[password]]@localhost:6379/0
    valkeys://[[username]:[password]]@localhost:6379/0
    unix://[[username]:[password]]@/path/to/socket.sock?db=0

.. _Valkey Developer Notes:

Valkey Developer Notes
=====================

To set up a local valkey instance, first set the socket path of the Valkey DB
in your YAML setting:

.. code:: yaml

   valkey:
     url: unix:///usr/local/searxng-valkey/run/valkey.sock?db=0

Then use the following commands to install the valkey instance (:ref:`manage
valkey.help`):

.. code:: sh

   $ ./manage valkey.build
   $ sudo -H ./manage valkey.install
   $ sudo -H ./manage valkey.addgrp "${USER}"
   # don't forget to logout & login to get member of group

