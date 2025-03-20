.. _settings plugins:

============
``plugins:``
============

.. attention::

   The ``enabled_plugins:`` section in SearXNG's settings no longer exists.
   There is no longer a distinction between built-in and external plugin, all
   plugins are registered via the settings in the ``plugins:`` section.

.. sidebar:: Further reading ..

   - :ref:`plugins admin`
   - :ref:`dev plugin`

In SearXNG, plugins can be registered in the :py:obj:`PluginStore
<searx.plugins.PluginStorage>` via a fully qualified class name.

A configuration (:py:obj:`PluginCfg <searx.plugins.PluginCfg>`) can be
transferred to the plugin, e.g. to activate it by default / *opt-in* or
*opt-out* from user's point of view.

Please note that some plugins, such as the :ref:`hostnames plugin` plugin,
require further configuration before they can be made available for selection.

built-in plugins
================

The built-in plugins are all located in the namespace `searx.plugins`.

.. code:: yaml

    plugins:

      searx.plugins.calculator.SXNGPlugin:
        active: true

      searx.plugins.hash_plugin.SXNGPlugin:
        active: true

      searx.plugins.self_info.SXNGPlugin:
        active: true

      searx.plugins.tracker_url_remover.SXNGPlugin:
        active: true

      searx.plugins.unit_converter.SXNGPlugin:
        active: true

      searx.plugins.ahmia_filter.SXNGPlugin:
        active: true

      searx.plugins.hostnames.SXNGPlugin:
        active: true

      searx.plugins.oa_doi_rewrite.SXNGPlugin:
        active: false

      searx.plugins.tor_check.SXNGPlugin:
        active: false


.. _settings external_plugins:

external plugins
================

.. _Only show green hosted results:
   https://github.com/return42/tgwf-searx-plugins/

SearXNG supports *external plugins* / there is no need to install one, SearXNG
runs out of the box.

- `Only show green hosted results`_
- ..
