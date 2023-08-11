.. _plugins generic:

===============
Plugins builtin
===============

.. sidebar:: Further reading ..

   - :ref:`dev plugin`

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

          JS & CSS dependencies

      {% for plgin in plugins %}

      * - {{plgin.name}}
        - {{(plgin.default_on and "y") or ""}}
        - {{plgin.description}}

          {% for dep in (plgin.js_dependencies + plgin.css_dependencies) %}
          | ``{{dep}}`` {% endfor %}

      {% endfor %}
