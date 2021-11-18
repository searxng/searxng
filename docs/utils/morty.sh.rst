
.. _morty: https://github.com/asciimoo/morty
.. _morty's README: https://github.com/asciimoo/morty
.. _Go: https://golang.org/

.. _morty.sh:

==================
``utils/morty.sh``
==================

.. sidebar:: further reading

   - :ref:`architecture`
   - :ref:`installation` (:ref:`nginx <installation nginx>` & :ref:`apache
     <installation apache>`)
   - :ref:`searxng morty`

To simplify installation and maintenance of a morty_ instance you can use the
script :origin:`utils/morty.sh`.  In most cases you will install morty_ simply by
running the command:

.. code::  bash

   sudo -H ./utils/morty.sh install all

The script adds a ``${SERVICE_USER}`` (default:``morty``) and installs morty_
into this user account:

#. Create a separated user account (``morty``).
#. Download and install Go_ binary in user's $HOME (``~morty``).
#. Install morty_ with the package management from Go_ (``go get -v -u
   github.com/asciimoo/morty``)
#. Setup a systemd service unit :origin:`[ref]
   <utils/templates/lib/systemd/system/morty.service>`
   (``/lib/systemd/system/morty.service``).

.. hint::

   To add morty to your SearXNG instance read chapter :ref:`searxng morty`.

Create user
===========

.. kernel-include:: $DOCS_BUILD/includes/morty.rst
   :start-after: START create user
   :end-before: END create user


Install go
==========

.. kernel-include:: $DOCS_BUILD/includes/morty.rst
   :start-after: START install go
   :end-before: END install go


Install morty
=============

Install morty software and systemd unit:

.. kernel-include:: $DOCS_BUILD/includes/morty.rst
   :start-after: START install morty
   :end-before: END install morty

.. kernel-include:: $DOCS_BUILD/includes/morty.rst
   :start-after: START install systemd unit
   :end-before: END install systemd unit

.. _morty.sh overview:

Overview
========

The ``--help`` output of the script is largely self-explanatory
(:ref:`toolboxing common`):

.. program-output:: ../utils/morty.sh --help

