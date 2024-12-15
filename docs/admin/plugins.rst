.. _plugins admin:

===============
List of plugins
===============

.. sidebar:: Further reading ..

   - :ref:`SearXNG settings <settings plugins>`
   - :ref:`dev plugin`
   - :ref:`builtin plugins`

Configuration defaults (at built time):

:DO: Default on

.. _configured plugins:

.. jinja:: searx

   .. flat-table:: Plugins configured at built time (defaults)
      :header-rows: 1
      :stub-columns: 1
      :widths: 3 1 9

      * - Name
        - DO
        - Description

      {% for plg in plugins %}

      * - {{plg.info.name}}
        - {{(plg.default_on and "y") or ""}}
        - {{plg.info.description}}

      {% endfor %}
