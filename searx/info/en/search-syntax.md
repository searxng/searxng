# Search syntax

SearXNG allows you to modify the default categories, engines and search language
via the search query.

Prefix `!` to set category and engine names.

Prefix: `:` to set the language.

Abbrevations of the engines and languages are also accepted.  Engine/category
modifiers are chainable and inclusive.  E.g. with {{search('!map !ddg !wp paris')}}
search in map category **and** duckduckgo **and** wikipedia for
`paris`.

See the {{link('preferences', 'preferences')}} for the list of engines,
categories and languages.

## Examples

Search in wikipedia for `paris`:

* {{search('!wp paris')}}
* {{search('!wikipedia paris')}}

Search in category `map` for `paris`:

* {{search('!map paris')}}

Image search:

* {{search('!images Wau Holland')}}

Custom language in wikipedia:

* {{search(':fr !wp Wau Holland')}}
