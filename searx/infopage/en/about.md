# About SearXNG

SearXNG is a [metasearch engine], aggregating the results of other
{{link('search engines', 'preferences')}} while not storing information about
its users.

The SearXNG project is driven by an open community, come join us on
Matrix if you have questions or just want to chat about SearXNG at [#searxng:matrix.org]

Make SearXNG better.

- You can improve SearXNG translations at [Weblate], or...
- Track development, send contributions, and report issues at [SearXNG sources].
- To get further information, visit SearXNG's project documentation at [SearXNG
  docs].

## Why use it?

- SearXNG may not offer you as personalized results as Google, but it doesn't
  generate a profile about you.
- SearXNG doesn't care about what you search for, never shares anything with a
  third-party, and it can't be used to compromise you.
- SearXNG is free software, the code is 100% open, and everyone is welcome to
  make it better.

If you do care about privacy, want to be a conscious user, or otherwise believe
in digital freedom, make SearXNG your default search engine or run it on your
own server!


## How do I set it as the default search engine?

SearXNG supports [OpenSearch].  For more information on changing your default
search engine, see your browser's documentation:

- [Firefox]
- [Microsoft Edge] - Behind the link, you will also find some useful instructions
  for Chrome and Safari.
- [Chromium]-based browsers only add websites that the user navigates to without
  a path.


## How does it work?

SearXNG is a fork from the well-known [searx] [metasearch engine] which was
inspired by the [Seeks project].  It provides basic privacy by mixing your
queries with searches on other platforms without storing search data.  SearXNG
can be added to your browser's search bar; moreover, it can be set as the
default search engine.

The {{link('stats page', 'stats')}} contains some useful anonymous usage
statistics about the engines used.

## How can I make it my own?

SearXNG appreciates your concern regarding logs, so take the code from the
[SearXNG sources] and run it yourself!

Add your instance to this [list of public
instances]({{get_setting('brand.public_instances')}}) to help other people
reclaim their privacy and make the internet freer.  The more decentralized the
internet is, the more freedom we have!


[SearXNG sources]: {{GIT_URL}}
[#searxng:matrix.org]: https://matrix.to/#/#searxng:matrix.org
[SearXNG docs]: {{get_setting('brand.docs_url')}}
[searx]: https://github.com/searx/searx
[metasearch engine]: https://en.wikipedia.org/wiki/Metasearch_engine
[Weblate]: https://weblate.bubu1.eu/projects/searxng/
[Seeks project]: https://beniz.github.io/seeks/
[OpenSearch]: https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md
[Firefox]: https://support.mozilla.org/en-US/kb/add-or-remove-search-engine-firefox
[Microsoft Edge]: https://support.microsoft.com/en-us/help/4028574/microsoft-edge-change-the-default-search-engine
[Chromium]: https://www.chromium.org/tab-to-search
