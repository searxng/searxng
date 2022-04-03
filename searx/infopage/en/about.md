# About MAGI

MAGI is a fork from the well-known metasearch engine searx, aggregating
the results of other {{link('search engines', 'preferences')}} while not
storing information about its users.

More about MAGI ...


## Why use it?

* MAGI may not offer you as personalised results as Google, but it doesn't
  generate a profile about you.

* MAGI doesn't care about what you search for, never shares anything with a
  third party, and it can't be used to compromise you.

* MAGI is free software, the code is 100% open and you can help to make it
  better. 
  
If you do care about privacy, want to be a conscious user, or otherwise believe
in digital freedom, make SearXNG your default search engine or run it on your
own server

## Technical details - How does it work?

MAGI is a [metasearch engine], inspired by the [seeks project].  It provides
basic privacy by mixing your queries with searches on other platforms without
storing search data. Queries are made using a POST request on every browser
(except Chromium-based browsers*).  Therefore they show up in neither our logs,
nor your url history. In the case of Chromium-based browser users there is an
exception: MAGI uses the search bar to perform GET requests.  MAGI can be
added to your browser's search bar; moreover, it can be set as the default
search engine.

## How to set as the default search engine?

MAGI supports [OpenSearch].  For more information on changing your default
search engine, see your browser's documentation:

* [Firefox]
* [Microsoft Edge]
* Chromium-based browsers [only add websites that the user navigates to without
  a path.](https://www.chromium.org/tab-to-search)

## Where to find anonymous usage statistics of this instance ?

{{link('Stats page', 'stats')}} contains some useful data about the engines
used.

[metasearch engine]: https://en.wikipedia.org/wiki/Metasearch_engine
[seeks project]: https://beniz.github.io/seeks/
[OpenSearch]: https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md
[Firefox]: https://support.mozilla.org/en-US/kb/add-or-remove-search-engine-firefox
[Microsoft Edge]: https://support.microsoft.com/en-us/help/4028574/microsoft-edge-change-the-default-search-engine
