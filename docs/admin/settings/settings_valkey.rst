.. _settings valkey:

===========
``valkey:``
===========

.. _Valkey:
    https://valkey.io
.. _Valkey-Installation:
    https://valkey.io/topics/installation/
.. _There are several ways to specify a database number:
    https://valkey-py.readthedocs.io/en/stable/connections.html#valkey.Valkey.from_url

A Valkey_ DB can be connected by an URL, in section :ref:`valkey db` you will
find a description to test your valkey connection in SearXNG.

``url`` : ``$SEARXNG_VALKEY_URL``
  URL to connect valkey database. `There are several ways to specify a database
  number`_::

    valkey://[[username]:[password]]@localhost:6379/0
    valkeys://[[username]:[password]]@localhost:6379/0
    unix://[[username]:[password]]@/path/to/socket.sock?db=0

  When using sockets, don't forget to check the access rights on the socket::

    ls -la /usr/local/searxng-valkey/run/valkey.sock
    srwxrwx--- 1 searxng-valkey searxng-valkey ... /usr/local/searxng-valkey/run/valkey.sock

  In this example read/write access is given to the *searxng-valkey* group.  To
  get access rights to valkey instance (the socket), your SearXNG (or even your
  developer) account needs to be added to the *searxng-valkey* group.


.. _Valkey Developer Notes:

Valkey Developer Notes
======================

To set up a local Valkey_ DB, set the URL connector in your YAML setting:

.. code:: yaml

   valkey:
     url: valkey://localhost:6379/0

To install a local Valkey_ DB from package manager read `Valkey-Installation`_
or use:

.. code:: sh

   $ ./utils/searxng.sh install valkey
   # restart your SearXNG instance
