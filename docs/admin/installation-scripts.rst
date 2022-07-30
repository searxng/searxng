.. _installation scripts:

===================
Installation Script
===================

.. sidebar:: Update the OS first!

   To avoid unwanted side effects, update your OS before installing SearXNG.

The following will install a setup as shown in :ref:`the reference architecture
<arch public>`.  First you need to get a clone of the repository.  The clone is only needed for
the installation procedure and some maintenance tasks.

.. sidebar:: further read

   - :ref:`toolboxing`

Jump to a folder that is readable by *others* and start to clone SearXNG,
alternatively you can create your own fork and clone from there.

.. code:: bash

   $ cd ~/Downloads
   $ git clone https://github.com/searxng/searxng.git searxng
   $ cd searxng

.. sidebar:: further read

   - :ref:`inspect searxng`

To install a SearXNG :ref:`reference setup <use_default_settings.yml>`
including a :ref:`uWSGI setup <architecture uWSGI>` as described in the
:ref:`installation basic` and in the :ref:`searxng uwsgi` section type:

.. code:: bash

   $ sudo -H ./utils/searxng.sh install all

.. attention::

   For the installation procedure, use a *sudoer* login to run the scripts.  If
   you install from ``root``, take into account that the scripts are creating a
   ``searxng`` user.  In the installation procedure this new created user does
   need read access to the cloned SearXNG repository, which is not the case if you clone
   it into a folder below ``/root``!

.. sidebar:: further read

   - :ref:`update searxng`

.. _caddy: https://hub.docker.com/_/caddy

When all services are installed and running fine, you can add SearXNG to your
HTTP server.  We do not have any preferences for the HTTP server, you can use
whatever you prefer.

We use caddy in our :ref:`docker image <installation docker>` and we have
implemented installation procedures for:

- :ref:`installation nginx`
- :ref:`installation apache`
