.. _settings plugins:

=======
Plugins
=======

.. sidebar:: Further reading ..

   - :ref:`plugins admin`
   - :ref:`dev plugin`
   - :ref:`builtin plugins`


The built-in plugins can be activated or deactivated via the settings
(:ref:`settings plugins`) and external plugins can be integrated into
SearXNG (:ref:`settings external_plugins`).


.. _settings plugins:

``plugins:`` (internal)
===============================

In :ref:`plugins admin` you find a complete list of all plugins, the default
configuration looks like:

.. code:: yaml

  plugins:
    - id: 'calculator'
      default_on: true
    - id: 'hash_plugin'
      default_on: true
    - id: 'self_info'
      default_on: true
    - id: 'tracker_url_remover'
      default_on: true
    - id: 'unit_converter'
      default_on: true
    - id: 'ahmia_filter'  # activation depends on outgoing.using_tor_proxy
      default_on: true

In order to disable a plugin by default, but still allow users to use it by enabling
it in their user settings, set ``default_on`` to ``false``. To completely disable a
plugin, you can set `inactive` to `true`.

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
     - id: only_show_green_results
       default_on: true
     # - fqn: mypackage.mymodule.MyPlugin
     # - fqn: mypackage.mymodule.MyOtherPlugin
     #   default_on: false

.. hint::

   ``only_show_green_results`` is an old plugin that was still implemented in
   the old style.  There is a legacy treatment for backward compatibility, but
   new plugins should be implemented as a :py:obj:`searx.plugins.Plugin` class.
