
.. _searxng.sh:

====================
``utils/searxng.sh``
====================

To simplify the installation and maintenance of a SearXNG instance you can use the
script :origin:`utils/searxng.sh`.

.. sidebar:: further reading

   - :ref:`architecture`
   - :ref:`installation`
   - :ref:`installation nginx`
   - :ref:`installation apache`

.. contents::
   :depth: 2
   :local:
   :backlinks: entry


Install
=======

In most cases you will install SearXNG simply by running the command:

.. code::  bash

   sudo -H ./utils/searxng.sh install all

The installation is described in chapter :ref:`installation basic`.

.. _searxng.sh overview:

Command Help
============

The ``--help`` output of the script is largely self-explanatory:

.. program-output:: ../utils/searxng.sh --help
