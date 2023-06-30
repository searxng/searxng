===============
Offline Concept
===============

.. sidebar:: offline engines

   - :ref:`demo offline engine`
   - :ref:`engine command`
   - :ref:`sql engines`
   - :ref:`nosql engines`
   - :py:obj:`searx.search.processors.offline`

To extend the functionality of SearXNG, offline engines are going to be
introduced.  An offline engine is an engine which does not need Internet
connection to perform a search and does not use HTTP to communicate.

Offline engines can be configured, by adding those to the `engines` list of
:origin:`settings.yml <searx/settings.yml>`.  An example skeleton for offline
engines can be found in :ref:`demo offline engine` (:origin:`demo_offline.py
<searx/engines/demo_offline.py>`).


Programming Interface
=====================

:py:func:`init(engine_settings=None) <searx.engines.demo_offline.init>`
  All offline engines can have their own init function to setup the engine before
  accepting requests. The function gets the settings from settings.yml as a
  parameter. This function can be omitted, if there is no need to setup anything
  in advance.

:py:func:`search(query, params) <searx.engines.demo_offline.searc>`
  Each offline engine has a function named ``search``.  This function is
  responsible to perform a search and return the results in a presentable
  format. (Where *presentable* means presentable by the selected result
  template.)

  The return value is a list of results retrieved by the engine.

Engine representation in ``/config``
  If an engine is offline, the attribute ``offline`` is set to ``True``.

.. _offline requirements:

Extra Dependencies
==================

If an offline engine depends on an external tool, SearXNG does not install it by
default.  When an administrator configures such engine and starts the instance,
the process returns an error with the list of missing dependencies.  Also,
required dependencies will be added to the comment/description of the engine, so
admins can install packages in advance.

If there is a need to install additional packages in *Python's Virtual
Environment* of your SearXNG instance you need to switch into the environment
(:ref:`searxng-src`) first, for this you can use :ref:`searxng.sh`::

  $ sudo utils/searxng.sh instance cmd bash
  (searxng-pyenv)$ pip install ...


Private engines (Security)
==========================

To limit the access to offline engines, if an instance is available publicly,
administrators can set token(s) for each of the :ref:`private engines`.  If a
query contains a valid token, then SearXNG performs the requested private
search.  If not, requests from an offline engines return errors.

