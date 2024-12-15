.. _settings plugins:

=======
Plugins
=======

.. sidebar:: Further reading ..

   - :ref:`plugins admin`
   - :ref:`dev plugin`
   - :ref:`builtin plugins`


The built-in plugins can be activated or deactivated via the settings
(:ref:`settings enabled_plugins`) and external plugins can be integrated into
SearXNG (:ref:`settings external_plugins`).


.. _settings enabled_plugins:

``enabled_plugins:`` (internal)
===============================

In :ref:`plugins admin` you find a complete list of all plugins, the default
configuration looks like:

.. code:: yaml

   enabled_plugins:
     - 'Basic Calculator'
     - 'Hash plugin'
     - 'Self Information'
     - 'Tracker URL remover'
     - 'Unit converter plugin'
     - 'Ahmia blacklist'


.. _settings external_plugins:

``plugins:`` (external)
=======================

SearXNG supports *external plugins* / there is no need to install one, SearXNG
runs out of the box.  But to demonstrate; in the example below we install the
SearXNG plugins from *The Green Web Foundation* `[ref]
<https://www.thegreenwebfoundation.org/news/searching-the-green-web-with-searx/>`__:

.. code:: bash

   $ sudo utils/searxng.sh instance cmd bash -c
   (searxng-pyenv)$ pip install git+https://github.com/return42/tgwf-searx-plugins

In the :ref:`settings.yml` activate the ``plugins:`` section and add module
``only_show_green_results`` from ``tgwf-searx-plugins``.

.. code:: yaml

   plugins:
     - only_show_green_results
     # - mypackage.mymodule.MyPlugin
     # - mypackage.mymodule.MyOtherPlugin

.. hint::

   ``only_show_green_results`` is an old plugin that was still implemented in
   the old style.  There is a legacy treatment for backward compatibility, but
   new plugins should be implemented as a :py:obj:`searx.plugins.Plugin` class.
