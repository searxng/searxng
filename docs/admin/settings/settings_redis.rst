.. _settings redis:

==========
``redis:``
==========

.. _Valkey: https://valkey.io

.. attention::

   SearXNG is switching from the Redis DB to Valkey_. The configuration
   description of Valkey_ in SearXNG can be found here: :ref:`settings
   <settings valkey>`.

If you have built and installed a local Redis DB for SearXNG, it is recommended
to uninstall it now and replace it with the installation of a Valkey_ DB.

.. _Redis Developer Notes:

Redis Developer Notes
=====================

To uninstall SearXNG's local Redis DB you can use:

.. code:: sh

   # stop your SearXNG instance
   $ ./utils/searxng.sh remove.redis

Remove the Redis DB in your YAML setting:

.. code:: yaml

   redis:
     url: unix:///usr/local/searxng-redis/run/redis.sock?db=0

To install Valkey_ read: :ref:`Valkey Developer Notes`
