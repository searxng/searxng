.. _installation basic:

=========================
Step by step installation
=========================

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

Step by step installation with virtualenv.  For Ubuntu, be sure to have enable
universe repository.

.. _install packages:

Install packages
================

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
   :start-after: START distro-packages
   :end-before: END distro-packages

.. hint::

   This installs also the packages needed by :ref:`searxng uwsgi`

.. _create searxng user:

Create user
===========

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
   :start-after: START create user
   :end-before: END create user

.. _searx-src:

Install SearXNG & dependencies
==============================

Start a interactive shell from new created user and clone searx:

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
   :start-after: START clone searxng
   :end-before: END clone searxng

In the same shell create *virtualenv*:

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
   :start-after: START create virtualenv
   :end-before: END create virtualenv

To install searx's dependencies, exit the SearXNG *bash* session you opened above
and restart a new.  Before install, first check if your *virtualenv* was sourced
from the login (*~/.profile*):

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
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

To create a initial ``/etc/searxng/settings.yml`` you can start with a copy of
the file :origin:`utils/templates/etc/searxng/settings.yml`.  This setup
:ref:`use default settings <settings use_default_settings>` from
:origin:`searx/settings.yml`.

For a *minimal setup*, configure like shown below – replace ``searx@$(uname
-n)`` with a name of your choice, set ``ultrasecretkey`` -- *and/or* edit
``/etc/searxng/settings.yml`` to your needs.

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
   :start-after: START searxng config
   :end-before: END searxng config

.. tabs::

  .. group-tab:: Use default settings

    .. literalinclude:: ../../utils/templates/etc/searxng/settings.yml
       :language: yaml

  .. group-tab:: searx/settings.yml

    .. literalinclude:: ../../searx/settings.yml
       :language: yaml


Check
=====

To check your SearXNG setup, optional enable debugging and start the *webapp*.
SearXNG looks at the exported environment ``$SEARXNG_SETTINGS_PATH`` for a
configuration file.

.. kernel-include:: $DOCS_BUILD/includes/searx.rst
   :start-after: START check searxng installation
   :end-before: END check searxng installation

If everything works fine, hit ``[CTRL-C]`` to stop the *webapp* and disable the
debug option in ``settings.yml``. You can now exit SearXNG user bash (enter exit
command twice).  At this point SearXNG is not demonized; uwsgi allows this.

