# Search syntax

SearXNG comes with a search syntax by which you can modify the categories,
engines, languages, and more.  See the {{link('preferences', 'preferences')}} for
the list of engines, categories, and languages.

## `!` Select engine and category

To set category and/or engine names, use a `!` prefix.  To give a few examples:

- Search Wikipedia for **paris**:

  - {{search('!wp paris')}}
  - {{search('!wikipedia paris')}}

- Search in category **map** for **paris**:

  - {{search('!map paris')}}

- Image search

  - {{search('!images Wau Holland')}}

Abbreviations of the engines and languages are also accepted.  Engine/category
modifiers are chainable and inclusive.  For example, {{search('!map !ddg !wp
paris')}} searches in the map category and searches DuckDuckGo and Wikipedia for **paris**.

## `:` Select language

To select a language filter use a `:` prefix.  To give an example:

- Search Wikipedia with a custom language:

  - {{search(':fr !wp Wau Holland')}}

## `!!<bang>` External bangs

SearXNG supports the external bangs from [DuckDuckGo].  To directly jump to a
external search page use the `!!` prefix.  To give an example:

- Search Wikipedia with a custom language:

  - {{search('!!wfr Wau Holland')}}

Please note that your search will be performed directly in the external search
engine.  SearXNG cannot protect your privacy with this.

[DuckDuckGo]: https://duckduckgo.com/bang

## `!!` automatic redirect

When including `!!` within your search query (separated by spaces), you will
automatically be redirected to the first result.  This behavior is comparable to
the "Feeling Lucky" feature from DuckDuckGo.  To give an example:

- Search for a query and get redirected to the first result

  - {{search('!! Wau Holland')}}

Please keep in mind that the result you are being redirected to can't be
verified for trustworthiness and SearXNG cannot protect your personal privacy
when using this feature.  Use it at your own risk.

## Special Queries

In the {{link('preferences', 'preferences')}} page you find keywords for
_special queries_.  To give a few examples:

- Generate a random UUID

  - {{search('random uuid')}}

- Find the average

  - {{search('avg 123 548 2.04 24.2')}}

- Show the _user agent_ of your browser (needs to be activated)

  - {{search('user-agent')}}

- Convert strings to different hash digests (needs to be activated)

  - {{search('md5 lorem ipsum')}}
  - {{search('sha512 lorem ipsum')}}
