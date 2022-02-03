
.. _search-syntax:

=============
Search syntax
=============

SearXNG allows you to modify the default categories, engines and search language
via the search query.

Prefix ``!``
  to set category/engine

Prefix: ``:``
  to set language

Abbrevations of the engines and languages are also accepted.  Engine/category
modifiers are chainable and inclusive. E.g. with ``!it !ddg !wp qwer`` search in
IT category **and** duckduckgo **and** wikipedia for ``qwer``.

See the ``/preferences page`` for the list of engines, categories and languages.

Examples
========

- Image search: ``!images Sagrada``
- Custom language in wikipedia: ``!wp :hu hackerspace``
- Search in wikipedia for ``qwer``:

  - ``!wp qwer`` or
  - ``!wikipedia qwer``

