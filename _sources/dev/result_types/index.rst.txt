.. _result types:

============
Result Types
============

To understand the typification of the results, let's take a brief look at the
structure of SearXNG ..  At its core, SearXNG is nothing more than an aggregator
that aggregates the results from various sources, renders them via templates and
displays them to the user.

The **sources** can be:

1. :ref:`engines <engine implementations>`
2. :ref:`plugins <dev plugin>`
3. :ref:`answerers <dev answerers>`

The sources provide the results, which are displayed in different **areas**
depending on the type of result. The areas are:

.. _area main results:

:ref:`area main results <main search results>`
  It is the main area in which -- as is typical for search engines -- the
  results that a search engine has found for the search term are displayed.

.. _area answer results:

:ref:`area answers <result_types.answer>`
  This area displays short answers that could be found for the search term.

.. _area info box:

:ref:`area info box <result_types.infobox>`
  An area in which additional information can be displayed, e.g. excerpts from
  wikipedia or other sources such as maps.

.. _area suggestions results:

:ref:`area suggestions <result_types.suggestion>`
  Suggestions for alternative search terms can be found in this area.  These can
  be clicked on and a search is carried out with these search terms.

.. _area corrections results:

:ref:`area corrections <result_types.corrections>`
  Results in this area are like the suggestion of alternative search terms,
  which usually result from spelling corrections

At this point it is important to note that all **sources** can contribute
results to all of the areas mentioned above.

In most cases, however, the :ref:`engines <engine implementations>` will fill
the *main results* and the :ref:`answerers <dev answerers>` will generally
provide the contributions for the *answer* area.  Not necessary to mention here
but for a better understanding: the plugins can also filter out or change
results from the main results area (e.g. the URL of the link).

The result items are organized in the :py:obj:`results.ResultContainer` and
after all sources have delivered their results, this container is passed to the
templating to build a HTML output.  The output is usually HTML, but it is also
possible to output the result lists as JSON or RSS feed. Thats quite all we need
to know before we dive into typification of result items.

.. hint::

   Typification of result items: we are at the very first beginng!

The first thing we have to realize is that there is no typification of the
result items so far, we have to build it up first .. and that is quite a big
task, which we will only be able to accomplish gradually.

The foundation for the typeless results was laid back in 2013 in the very first
commit :commit:`ae9fb1d7d`, and the principle has not changed since then.  At
the time, the approach was perfectly adequate, but we have since evolved and the
demands on SearXNG increase with every feature request.

**Motivation:** in the meantime, it has become very difficult to develop new
features that require structural changes and it is especially hard for newcomers
to find their way in this typeless world.  As long as the results are only
simple key/value dictionaries, it is not even possible for the IDEs to support
the application developer in his work.

**Planning:** The procedure for subsequent typing will have to be based on the
circumstances ..

.. attention::

   As long as there is no type defined for a kind of result the HTML template
   specify what the properties of a type are.

   In this sense, you will either find a type definition here in the
   documentation or, if this does not yet exist, a description of the HTML
   template.


.. toctree::
   :maxdepth: 2

   base_result
   main_result
   answer
   correction
   suggestion
   infobox
