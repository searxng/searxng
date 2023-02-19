.. _dev plugin:

=======
Plugins
=======

.. sidebar:: Further reading ..

   - :ref:`plugins generic`

Plugins can extend or replace functionality of various components of searx.

Example plugin
==============

.. code:: python

   name = 'Example plugin'
   description = 'This plugin extends the suggestions with the word "example"'
   default_on = False  # disabled by default

   js_dependencies = tuple()  # optional, list of static js files
   css_dependencies = tuple()  # optional, list of static css files


   # attach callback to the post search hook
   #  request: flask request object
   #  ctx: the whole local context of the post search hook
   def post_search(request, search):
       search.result_container.suggestions.add('example')
       return True

External plugins
================

SearXNG supports *external plugins* / there is no need to install one, SearXNG
runs out of the box.  But to demonstrate; in the example below we install the
SearXNG plugins from *The Green Web Foundation* `[ref]
<https://www.thegreenwebfoundation.org/news/searching-the-green-web-with-searx/>`__:

.. code:: bash

   $ sudo utils/searxng.sh instance cmd bash
   (searxng-pyenv)$ pip install git+https://github.com/return42/tgwf-searx-plugins

In the :ref:`settings.yml` activate the ``plugins:`` section and add module
``only_show_green_results`` from ``tgwf-searx-plugins``.

.. code:: yaml

   plugins:
     ...
     - only_show_green_results
     ...


Plugin entry points
===================

Entry points (hooks) define when a plugin runs. Right now only three hooks are
implemented. So feel free to implement a hook if it fits the behaviour of your
plugin. A plugin doesn't need to implement all the hooks.


.. py:function:: pre_search(request, search) -> bool

   Runs BEFORE the search request.

   `search.result_container` can be changed.

   Return a boolean:

   * True to continue the search
   * False to stop the search

   :param flask.request request:
   :param searx.search.SearchWithPlugins search:
   :return: False to stop the search
   :rtype: bool


.. py:function:: post_search(request, search) -> None

   Runs AFTER the search request.

   :param flask.request request: Flask request.
   :param searx.search.SearchWithPlugins search: Context.


.. py:function:: on_result(request, search, result) -> bool

   Runs for each result of each engine.

   `result` can be changed.

   If `result["url"]` is defined, then `result["parsed_url"] = urlparse(result['url'])`

   .. warning::
      `result["url"]` can be changed, but `result["parsed_url"]` must be updated too.

   Return a boolean:

   * True to keep the result
   * False to remove the result

   :param flask.request request:
   :param searx.search.SearchWithPlugins search:
   :param typing.Dict result: Result, see - :ref:`engine results`
   :return: True to keep the result
   :rtype: bool
