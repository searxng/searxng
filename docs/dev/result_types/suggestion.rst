.. _result_types.suggestion:

==================
Suggestion Results
==================

.. hint::

   There is still no typing for these result items. The templates can be used as
   orientation until the final typing is complete.

The :ref:`area suggestions results` shows the user alternative search terms.

A result of this type is a very simple dictionary with only one key/value pair

.. code:: python

   {"suggestion" : "lorem ipsum .."}

From this simple dict another dict is build up:

.. code:: python

   {"url" : "!bang lorem ipsum ..", "title": "lorem ipsum" }

and used in the template :origin:`suggestions.html
<searx/templates/simple/elements/suggestions.html>`:

.. code:: python

   # use RawTextQuery to get the suggestion URLs with the same bang
   {"url" : "!bang lorem ipsum ..", "title": "lorem ipsum" }

title : :py:class:`str`
  Suggested search term

url : :py:class:`str`
  Not really an URL, its the value to insert in a HTML form for a SearXNG query.
