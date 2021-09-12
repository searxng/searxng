
.. _search-syntax:

=============
Search syntax
=============

SearXNG allows you to modify the default categories, engines and search language
via the search query.

Prefix ``!``
  to set Category/engine

Prefix: ``:``
  to set language

Prefix: ``?``
  to add engines and categories to the currently selected categories

Abbrevations of the engines and languages are also accepted.  Engine/category
modifiers are chainable and inclusive (e.g. with :search:`!it !ddg !wp qwer
<?q=%21it%20%21ddg%20%21wp%20qwer>` search in IT category **and** duckduckgo
**and** wikipedia for ``qwer``).

See the :search:`/preferences page <preferences>` for the list of engines,
categories and languages.

Examples
========

Search in wikipedia for ``qwer``:

- :search:`!wp qwer <?q=%21wp%20qwer>` or
- :search:`!wikipedia qwer :search:<?q=%21wikipedia%20qwer>`

Image search:

- :search:`!images Cthulhu <?q=%21images%20Cthulhu>`

Custom language in wikipedia:

- :search:`:hu !wp hackerspace <?q=%3Ahu%20%21wp%20hackerspace>`

Multilingual Search
===================

SearXNG does not support true multilingual search.
You have to use the language prefix in your search query when searching in a different language.

But there is a workaround:
By adding a new search engine with a different language, SearXNG will search in your default and other language.

Example configuration in settings.yml for a German and English speaker:
 .. code-block:: yaml

    search:
        language : "de"
        ...

    engines:
      - name : google english
        engine : google
        language : english
        ...

When searching, the default google engine will return German results and "google english" will return English results.
