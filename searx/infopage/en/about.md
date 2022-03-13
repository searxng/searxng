# About SearXNG

SearXNG is a fork from the well-known [searx] [metasearch engine], aggregating
the results of other {{link('search engines', 'preferences')}} while not
storing information about its users.

More about SearXNG ...

* [SearXNG sources]({{GIT_URL}})
* [weblate]


## Why use it?

* SearXNG may not offer you as personalised results as Google, but it doesn't
  generate a profile about you.

* SearXNG doesn't care about what you search for, never shares anything with a
  third party, and it can't be used to compromise you.

* SearXNG is free software, the code is 100% open and you can help to make it
  better.  See more on [SearXNG sources]({{GIT_URL}}).

If you do care about privacy, want to be a conscious user, or otherwise believe
in digital freedom, make SearXNG your default search engine or run it on your
own server

## Technical details - How does it work?

SearXNG is a [metasearch engine], inspired by the [seeks project].  It provides
basic privacy by mixing your queries with searches on other platforms without
storing search data. Queries are made using a POST request on every browser
(except Chromium-based browsers*).  Therefore they show up in neither our logs,
nor your url history. In the case of Chromium-based browser users there is an
exception: searx uses the search bar to perform GET requests.  SearXNG can be
added to your browser's search bar; moreover, it can be set as the default
search engine.

## How to set as the default search engine?

SearXNG supports [OpenSearch].  For more information on changing your default
search engine, see your browser's documentation:

* [Firefox]
* [Microsoft Edge]
* Chromium-based browsers [only add websites that the user navigates to without
  a path.](https://www.chromium.org/tab-to-search)

## Where to find anonymous usage statistics of this instance ?

{{link('Stats page', 'stats')}} contains some useful data about the engines
used.

## How can I make it my own?

SearXNG appreciates your concern regarding logs, so take the code from the
[SearXNG project]({{GIT_URL}}) and run it yourself!

Add your instance to this [list of public
instances]({{get_setting('brand.public_instances')}}) to help other people
reclaim their privacy and make the Internet freer!  The more decentralized the
Internet is, the more freedom we have!

## Where are the docs & code of this instance?

See the [SearXNG docs]({{get_setting('brand.docs_url')}}) and [SearXNG
sources]({{GIT_URL}})

[searx]: https://github.com/searx/searx
[metasearch engine]: https://en.wikipedia.org/wiki/Metasearch_engine
[weblate]: https://weblate.bubu1.eu/projects/searxng/
[seeks project]: https://beniz.github.io/seeks/
[OpenSearch]: https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md
[Firefox]: https://support.mozilla.org/en-US/kb/add-or-remove-search-engine-firefox
[Microsoft Edge]: https://support.microsoft.com/en-us/help/4028574/microsoft-edge-change-the-default-search-engine
