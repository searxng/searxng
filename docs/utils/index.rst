.. _searx_utils:
.. _toolboxing:

===================
Admin's tooling box
===================

In the folder :origin:`utils/` we maintain some tools useful for administrators.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   searx.sh
   filtron.sh
   morty.sh
   lxc.sh

.. _toolboxing common:

Common commands & environment
=============================

Scripts to maintain services often dispose of common commands and environments.

``shell`` : command
  Opens a shell from the service user ``${SERVICE_USSR}``, very helpful for
  troubleshooting.

``inspect service`` : command
  Shows status and log of the service, most often you have a option to enable
  more verbose debug logs.  Very helpful for debugging, but be careful not to
  enable debugging in a production environment!

``FORCE_TIMEOUT`` : environment
  Sets timeout for interactive prompts. If you want to run a script in batch
  job, with defaults choices, set ``FORCE_TIMEOUT=0``.  By example; to install a
  reverse proxy for filtron on all containers of the :ref:`SearXNG suite
  <lxc-searx.env>` use ::

    sudo -H ./utils/lxc.sh cmd -- FORCE_TIMEOUT=0 ./utils/filtron.sh apache install

.. _toolboxing setup:

Tooling box setup
=================

The main setup is done in the :origin:`.config.sh` (read also :ref:`settings
global`).

.. literalinclude:: ../../.config.sh
   :language: bash
