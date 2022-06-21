.. _installation basic:

=========================
Step by step installation
=========================

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry


In this section we show the setup of a SearXNG instance that will be installed
by the :ref:`installation scripts`.

.. _install packages:

Install packages
================

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START distro-packages
   :end-before: END distro-packages

.. hint::

   This installs also the packages needed by :ref:`searxng uwsgi`

.. _create searxng user:

Create user
===========

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START create user
   :end-before: END create user

.. _searxng-src:

Install SearXNG & dependencies
==============================

Start a interactive shell from new created user and clone SearXNG:

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START clone searxng
   :end-before: END clone searxng

In the same shell create *virtualenv*:

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START create virtualenv
   :end-before: END create virtualenv

To install SearXNG's dependencies, exit the SearXNG *bash* session you opened above
and start a new one.  Before installing, check if your *virtualenv* was sourced
from the login (*~/.profile*):

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START manage.sh update_packages
   :end-before: END manage.sh update_packages

.. tip::

   Open a second terminal for the configuration tasks and leave the ``(searx)$``
   terminal open for the tasks below.


.. _use_default_settings.yml:

Configuration
=============

.. sidebar:: ``use_default_settings: True``

   - :ref:`settings global`
   - :ref:`settings location`
   - :ref:`settings use_default_settings`
   - :origin:`/etc/searxng/settings.yml <utils/templates/etc/searxng/settings.yml>`

To create a initial ``/etc/searxng/settings.yml`` we recommend to start with a
copy of the file :origin:`utils/templates/etc/searxng/settings.yml`.  This setup
:ref:`use default settings <settings use_default_settings>` from
:origin:`searx/settings.yml` and is shown in the tab *"Use default settings"*
below. This setup:

- enables :ref:`limiter <limiter>` to protect against bots
- enables :ref:`image proxy <image_proxy>` for better privacy
- enables :ref:`cache busting <static_use_hash>` to save bandwith

Modify the ``/etc/searxng/settings.yml`` to your needs:

.. tabs::

  .. group-tab:: Use default settings

     .. literalinclude:: ../../utils/templates/etc/searxng/settings.yml
        :language: yaml
        :end-before: # hostname_replace:

     To see the entire file jump to :origin:`utils/templates/etc/searxng/settings.yml`

  .. group-tab:: searx/settings.yml

     .. literalinclude:: ../../searx/settings.yml
        :language: yaml
        :end-before: # hostname_replace:

     To see the entire file jump to :origin:`searx/settings.yml`

For a *minimal setup* you need to set ``server:secret_key``.

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START searxng config
   :end-before: END searxng config


Check
=====

To check your SearXNG setup, optional enable debugging and start the *webapp*.
SearXNG looks at the exported environment ``$SEARXNG_SETTINGS_PATH`` for a
configuration file.

.. kernel-include:: $DOCS_BUILD/includes/searxng.rst
   :start-after: START check searxng installation
   :end-before: END check searxng installation

If everything works fine, hit ``[CTRL-C]`` to stop the *webapp* and disable the
debug option in ``settings.yml``. You can now exit SearXNG user bash session (enter exit
command twice).  At this point SearXNG is not demonized; uwsgi allows this.

