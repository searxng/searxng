.. _configured engines:

==================
Configured Engines
==================

.. sidebar:: Further reading ..

   - :ref:`settings categories_as_tabs`
   - :ref:`engines-dev`
   - :ref:`settings engines`
   - :ref:`general engine configuration`

.. jinja:: searx

   SearXNG supports {{engines | length}} search engines of which
   {{enabled_engine_count}} are enabled by default.

   Engines can be assigned to multiple :ref:`categories <engine categories>`.
   The UI displays the tabs that are configured in :ref:`categories_as_tabs
   <settings categories_as_tabs>`.  In addition to these UI categories (also
   called *tabs*), engines can be queried by their name or the categories they
   belong to, by using a :ref:`\!bing syntax <search-syntax>`.

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

.. jinja:: searx

   {% for category, engines in categories_as_tabs.items() %}

   tab ``!{{category.replace(' ', '_')}}``
   ---------------------------------------

   {% for group, group_bang, engines in engines | group_engines_in_tab %}

   {% if loop.length > 1 %}
   {% if group_bang %}group ``{{group_bang}}``{% else %}{{group}}{% endif %}
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   {% endif %}

   .. flat-table::
      :header-rows: 2
      :stub-columns: 1
      :widths: 10 1 10 1 1 1 1 1 1 1

      * - :cspan:`5` Engines configured by default (in :ref:`settings.yml <engine settings>`)
        - :cspan:`3` :ref:`Supported features <engine file>`

      * - Name
        - !bang
        - Module
        - Disabled
        - Timeout
        - Weight
        - Paging
        - Locale
        - Safe search
        - Time range

      {% for mod in engines %}

      * - `{{mod.name}} <{{mod.about and mod.about.website}}>`_
          {%- if mod.about and  mod.about.language %}
          ({{mod.about.language | upper}})
          {%- endif %}
        - ``!{{mod.shortcut}}``
        - {%- if 'searx.engines.' + mod.__name__ in documented_modules %}
          :py:mod:`~searx.engines.{{mod.__name__}}`
          {%- else %}
          :origin:`{{mod.__name__}} <searx/engines/{{mod.__name__}}.py>`
          {%- endif %}
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
     {% endfor %}
