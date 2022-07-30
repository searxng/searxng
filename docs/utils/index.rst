.. _searx_utils:
.. _toolboxing:

==================
DevOps tooling box
==================

In the folder :origin:`utils/` we maintain some tools useful for administrators
and developers.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   searxng.sh
   lxc.sh

Common command environments
===========================

The scripts in our tooling box often dispose of common environments:

``FORCE_TIMEOUT`` : environment
  Sets timeout for interactive prompts. If you want to run a script in batch
  job, with defaults choices, set ``FORCE_TIMEOUT=0``.  By example; to install a
  SearXNG server and nginx proxy on all containers of the :ref:`SearXNG suite
  <lxc-searxng.env>` use::

    sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/searxng.sh install all
    sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/searxng.sh install nginx
