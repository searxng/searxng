
.. _how to search:

=============
How to search
=============

.. jinja:: searx

   SearXNG supports {{engines | length}} search engines.
   Since searching all of these for every single query would be too
   slow SearXNG groups its engines into categories.

The most important categories are easily accessible as tabs on the
search result page (just like with the mainstream search engines).

Within a category engines can be enabled or disabled from the
:guilabel:`Engines` tab in the preferences (you can access the
preferences via the :guilabel:`Preferences` link in the Oscar theme
and the :guilabel:`☰` link in the Simple theme). When you search
in a category only the enabled engines will be searched.

Searching multiple categories
=============================

In the :guilabel:`User Interface` preferences you can
disabled :guilabel:`Search on category select` which
changes the tabs on the search result pages into checkboxes,
letting you search multiple engines at once.
(Note: If you have JavaScript disabled that is already the case.)

.. _bang syntax:

Bang syntax
-----------

Alternatively you can use our *bang syntax*.
For example searching for ``cats !images !videos``
searches all enabled engines in the Images category
and all enabled engines in the Videos category.
Note that the order of the bangs does not matter,
e.g. ``!videos cats !images`` yields the same results.

.. TODO: mention bang autocompletion with JavaScript

Searching specific engines
==========================

Instead of casting a wide net you can also specifically target engines.
In the engine preferences you can find a "shortcut" for each engine,
which you can use with the same bang syntax you know from categories.
For example searching for ``!ddg ducks`` searches for "ducks" only in
the DuckDuckGo search engine.

Note that you can combine category bangs with engine bangs, so e.g.
the query ``!ddg !images ducks`` searches the DuckDuckGo engine along
with all enabled engines in the images category for "ducks".
(For engine bangs it does not matter if the engine is enabled or
disabled within its category, if you ask for an engine explicitly it is
always searched.)

Searching in a language
=======================

In the language select after the search box you can choose which
language you want your search results to be in. Note that no matter
what you choose you might still get results in other languages (mostly
English) because not every engine supports language selection (you can
see which ones do in the engine preferences).

Alternatively you can use the special syntax ``:es gato`` to search for
"gato" in Spanish, ``:fr chat`` to search for "chat" in French, ``:de
katze`` to search for "katze" in German, etc.

.. TODO: how do you find the language code for a language?

Note that unlike the bang syntax the language codes cannot be combined.
Searching for ``:es :fr cat`` does **not** search for "cat" in Spanish
and French it only searches in French (the last language code is used).

Also note that searching for ``:es gato`` changes your default search
language to Spanish so subsequent searches will also be in Spanish
(until you change the language in the language select or use another
language code).
