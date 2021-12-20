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

   {% for category, engines in engines.items() | groupby('1.categories.0') %}

   {{category}} search engines
   ---------------------------------------

   .. flat-table::
      :header-rows: 2
      :stub-columns: 1

      * - :cspan:`5` Engines configured by default (in :ref:`settings.yml <engine settings>`)
        - :cspan:`3` :ref:`Supported features <engine file>`

      * - Name
        - Shortcut
        - Engine
        - Disabled
        - Timeout
        - Weight
        - Paging
        - Language
        - Safe search
        - Time range

      {% for name, mod in engines %}

      * - `{{name}} <{{mod.about and mod.about.website}}>`_
        - ``!{{mod.shortcut}}``
        - {{mod.__name__}}
        - {{(mod.disabled and "y") or ""}}
        - {{mod.timeout}}
        - {{mod.weight or 1 }}
        {% if mod.engine_type == 'online' %}
        - {{(mod.paging and "y") or ""}}
        - {{(mod.language_support and "y") or ""}}
        - {{(mod.safesearch and "y") or ""}}
        - {{(mod.time_range_support and "y") or ""}}
        {% else %}
        - :cspan:`3` not applicable ({{mod.engine_type}})
        {% endif %}

     {% endfor %}
     {% endfor %}
