
.. _searx.sh:

==================
``utils/searx.sh``
==================

.. sidebar:: further reading

   - :ref:`architecture`
   - :ref:`installation`
   - :ref:`installation nginx`
   - :ref:`installation apache`

To simplify installation and maintenance of a SearXNG instance you can use the
script :origin:`utils/searx.sh`.

Install
=======

In most cases you will install SearXNG simply by running the command:

.. code::  bash

   sudo -H ./utils/searx.sh install all

The script adds a ``${SERVICE_USER}`` (default:``searx``) and installs SearXNG
into this user account.  The installation is described in chapter
:ref:`installation basic`.

.. _intranet reverse proxy:

Overview
========

The ``--help`` output of the script is largely self-explanatory
(:ref:`toolboxing common`):

.. program-output:: ../utils/searx.sh --help
