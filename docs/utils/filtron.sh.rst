
.. _filtron.sh:

====================
``utils/filtron.sh``
====================

.. sidebar:: further reading

   - :ref:`searxng filtron`
   - :ref:`architecture`
   - :ref:`installation` (:ref:`nginx <installation nginx>` & :ref:`apache
     <installation apache>`)

.. _Go: https://golang.org/
.. _filtron: https://github.com/searxng/filtron
.. _filtron README: https://github.com/searxng/filtron/blob/master/README.md

To simplify installation and maintenance of a filtron instance you can use the
script :origin:`utils/filtron.sh`.  In most cases you will install filtron_
simply by running the command:

.. code::  bash

   sudo -H ./utils/filtron.sh install all

The script adds a ``${SERVICE_USER}`` (default:``filtron``) and installs filtron_
into this user account:

#. Create a separated user account (``filtron``).
#. Download and install Go_ binary in user's $HOME (``~filtron``).
#. Install filtron with the package management from Go_ (``go get -v -u
   github.com/searxng/filtron``)
#. Setup a proper rule configuration :origin:`[ref]
   <utils/templates/etc/filtron/rules.json>` (``/etc/filtron/rules.json``).
#. Setup a systemd service unit :origin:`[ref]
   <utils/templates/lib/systemd/system/filtron.service>`
   (``/lib/systemd/system/filtron.service``).


Create user
===========

.. kernel-include:: $DOCS_BUILD/includes/filtron.rst
   :start-after: START create user
   :end-before: END create user


Install go
==========

.. kernel-include:: $DOCS_BUILD/includes/filtron.rst
   :start-after: START install go
   :end-before: END install go


Install filtron
===============

Install :origin:`rules.json <utils/templates/etc/filtron/rules.json>` at
``/etc/filtron/rules.json`` (see :ref:`Sample configuration of filtron`) and
install filtron software and systemd unit:

.. kernel-include:: $DOCS_BUILD/includes/filtron.rst
   :start-after: START install filtron
   :end-before: END install filtron

.. kernel-include:: $DOCS_BUILD/includes/filtron.rst
   :start-after: START install systemd unit
   :end-before: END install systemd unit

.. _filtron.sh overview:

Overview
========

The ``--help`` output of the script is largely self-explanatory
(:ref:`toolboxing common`):

.. program-output:: ../utils/filtron.sh --help
