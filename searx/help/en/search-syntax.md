# Search syntax

SearXNG allows you to modify the default categories, engines and search language
via the search query.

Prefix `!` to set Category/engine.

Prefix: `:` to set the language.

Abbrevations of the engines and languages are also accepted.  Engine/category
modifiers are chainable and inclusive (e.g. with [!it !ddg !wp
qwer]($search?q=!it+!ddg+!wp+qwer)) search in IT category **and** duckduckgo
**and** wikipedia for ``qwer``).

See the [preferences]($preferences) for the list of engines,
categories and languages.

## Examples

Search in wikipedia for `qwer`:

* [!wp qwer]($search?q=!wp+qwer)
* [!wikipedia qwer]($search?q=!wikipedia+qwer)

Image search:

* [!images Cthulu]($search?q=!images+Cthulu)

Custom language in wikipedia:

* [:hu !wp hackerspace]($search?q=:hu+!wp+hackerspace)
