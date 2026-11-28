.. _searx_utils:
.. _toolboxing:

==================
DevOps tooling box
==================

In the folder :origin:`utils/` we maintain some tools useful for administrators
and developers.

.. toctree::
   :maxdepth: 2

   searxng.sh


Common command environments
===========================

The scripts in our tooling box often dispose of common environments:

.. _FORCE_TIMEOUT:

``FORCE_TIMEOUT`` : environment
  Sets timeout for interactive prompts. If you want to run a script in batch
  job, with defaults choices, set ``FORCE_TIMEOUT=0``.  By example; to install a
  SearXNG server and nginx proxy use::

    $ FORCE_TIMEOUT=0 ./utils/searxng.sh install all
    $ FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx
