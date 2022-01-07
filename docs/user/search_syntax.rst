
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
