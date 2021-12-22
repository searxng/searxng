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

   SearXNG supports {{engines | length}} search engines (of which {{enabled_engine_count}} are enabled by default).

   {% for category, engines in categories_as_tabs.items() %}

   {{category}} search engines
   ---------------------------------------

   {% for group, engines in engines | group_engines_in_tab %}

   {% if loop.length > 1 %}
   {{group}}
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   {% endif %}

   .. flat-table::
      :header-rows: 2
      :stub-columns: 1

      * - :cspan:`5` Engines configured by default (in :ref:`settings.yml <engine settings>`)
        - :cspan:`3` :ref:`Supported features <engine file>`

      * - Name
        - Shortcut
        - Module
        - Disabled
        - Timeout
        - Weight
        - Paging
        - Language
        - Safe search
        - Time range

      {% for mod in engines %}

      * - `{{mod.name}} <{{mod.about and mod.about.website}}>`_
        - ``!{{mod.shortcut}}``
        - {%- if 'searx.engines.' + mod.__name__ in documented_modules %}
          :py:mod:`~searx.engines.{{mod.__name__}}`
          {%- else %}
          :origin:`{{mod.__name__}} <searx/engines/{{mod.__name__}}.py>`
          {%- endif %}
        - {{(mod.disabled and "y") or ""}}
          {%- if mod.about and  mod.about.language %}
          ({{mod.about.language | upper}})
          {%- endif %}
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
     {% endfor %}
