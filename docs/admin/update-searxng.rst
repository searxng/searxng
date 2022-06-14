===================
SearXNG maintenance
===================

.. sidebar:: further read

   - :ref:`toolboxing`
   - :ref:`uWSGI maintenance`

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

.. _update searxng:

How to update
=============

How to update depends on the :ref:`installation` method.  If you have used the
:ref:`installation scripts`, use ``update`` command from the :ref:`searxng.sh`
script.

.. code:: sh

    sudo -H ./utils/searxng.sh instance update

.. _inspect searxng:

How to inspect & debug
======================

How to debug depends on the :ref:`installation` method.  If you have used the
:ref:`installation scripts`, use ``inspect`` command from the :ref:`searxng.sh`
script.

.. code:: sh

    sudo -H ./utils/searxng.sh instance inspect
