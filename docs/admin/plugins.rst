.. _plugins admin:

===============
List of plugins
===============

Further reading ..

- :ref:`Zhensa settings <settings plugins>`
- :ref:`dev plugin`

.. _configured plugins:

.. jinja:: zhensa

   .. flat-table:: Plugins configured at built time (defaults)
      :header-rows: 1
      :stub-columns: 1
      :widths: 3 1 9

      * - Name
        - Active
        - Description

      {% for plg in plugins %}

      * - {{plg.info.name}}
        - {{(plg.active and "yes") or "no"}}
        - {{plg.info.description}}

      {% endfor %}
