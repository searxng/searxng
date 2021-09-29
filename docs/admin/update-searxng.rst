.. _update searxng:

=============
How to update
=============

How to update depends on the :ref:`installation` method.  If you have used the
:ref:`installation scripts`, use ``update`` command from the scripts.

**Update** :ref:`SearXNG service <searxng.sh>`

.. code:: sh

    sudo -H ./utils/searxng.sh update searxng

**Update** :ref:`filtron reverse proxy <filtron.sh>`

.. code:: sh

    sudo -H ./utils/filtron.sh update filtron

**Update** :ref:`result proxy <morty.sh>`

.. code:: bash

   $ sudo -H ./utils/morty.sh update morty

.. _inspect searxng:

======================
How to inspect & debug
======================

.. sidebar:: further read

   - :ref:`toolboxing`
   - :ref:`Makefile`

How to debug depends on the :ref:`installation` method.  If you have used the
:ref:`installation scripts`, use ``inspect`` command from the scripts.

**Inspect** :ref:`SearXNG service <searxng.sh>`

.. code:: sh

    sudo -H ./utils/searxng.sh inspect service

**Inspect** :ref:`filtron reverse proxy <filtron.sh>`

.. code:: sh

    sudo -H ./utils/filtron.sh inspect service

**Inspect** :ref:`result proxy <morty.sh>`

.. code:: bash

   $ sudo -H ./utils/morty.sh inspect service

