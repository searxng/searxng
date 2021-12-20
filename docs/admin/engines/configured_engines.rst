.. _configured engines:

==================
Configured Engines
==================

.. sidebar:: Further reading ..

   - :ref:`engines-dev`
   - :ref:`settings engine`

Explanation of the :ref:`general engine configuration` shown in the table
:ref:`configured engines`.

.. jinja:: searx

   .. flat-table::
      :header-rows: 2
      :stub-columns: 1

      * - :cspan:`6` Engines configured by default (in :ref:`settings.yml <engine settings>`)
        -
        - :cspan:`3` :ref:`Supported features <engine file>`

      * - Name
        - Shortcut
        - Engine
        - Disabled
        - Timeout
        - Weight
        - Display errors
        - Categories
        - Paging
        - Language
        - Safe search
        - Time range
        - Engine type

      {% for name, mod in engines.items() %}

      * - `{{name}} <{{mod.about and mod.about.website}}>`_
        - ``!{{mod.shortcut}}``
        - {{mod.__name__}}
        - {{(mod.disabled and "y") or ""}}
        - {{mod.timeout}}
        - {{mod.weight or 1 }}
        - {{(mod.display_error_messages and "y") or ""}}
        - {{", ".join(mod.categories)}}
        - {{(mod.paging and "y") or ""}}
        - {{(mod.language_support and "y") or ""}}
        - {{(mod.safesearch and "y") or ""}}
        - {{(mod.time_range_support and "y") or ""}}
        - {{mod.engine_type or ""}}

     {% endfor %}

