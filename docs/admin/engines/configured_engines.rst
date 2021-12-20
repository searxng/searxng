.. _configured engines:

==================
Configured Engines
==================

.. sidebar:: Further reading ..

   - :ref:`engines-dev`
   - :ref:`settings engine`

Explanation of the :ref:`general engine configuration` shown in the table
:ref:`configured engines`.

.. table:: The legend for the following table
   :width: 100%

   ========================= =================================
   :ref:`engine settings`    :ref:`engine file`
   ------------------------- ---------------------------------
   Name                      Categories
   ------------------------- ---------------------------------
   Engine                    Paging support
   ------------------------- ---------------------------------
   Shortcut                  Language support
   Timeout                   Time range support
   Disabled                  Engine type
   ------------------------- ---------------------------------
   Safe search
   ------------------------- ---------------------------------
   Weigth
   ------------------------- ---------------------------------
   Show errors
   ========================= =================================

.. jinja:: searx

   .. flat-table:: Engines configured at built time (defaults)
      :header-rows: 1
      :stub-columns: 2

      * - Name
        - Shortcut
        - Engine
        - Timeout
        - Categories
        - Paging
        - Language
        - Safe search
        - Disabled
        - Time range
        - Engine type
        - Weight
        - Display errors

      {% for name, mod in engines.items() %}

      * - `{{name}} <{{mod.about and mod.about.website}}>`_
        - !{{mod.shortcut}}
        - {{mod.__name__}}
        - {{mod.timeout}}
        - {{", ".join(mod.categories)}}
        - {{(mod.paging and "y") or ""}}
        - {{(mod.language_support and "y") or ""}}
        - {{(mod.safesearch and "y") or ""}}
        - {{(mod.disabled and "y") or ""}}
        - {{(mod.time_range_support and "y") or ""}}
        - {{mod.engine_type or ""}}
        - {{mod.weight or 1 }}
        - {{(mod.display_error_messages and "y") or ""}}

     {% endfor %}

