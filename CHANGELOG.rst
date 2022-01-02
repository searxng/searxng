1.0.0 2021.03.27
================

Core
~~~~

- drop support for Python 3.5 ( #2459 )
- add support for Python 3.9 ( #2397 #2459 )
- update Python dependencies ( #2428 #2459 #2206 ) ⚠️ pyopenssl is not longer required
- automatic update of searx.data ( #2555 #2585 #2595 #2592 #2600 )
- update searx.data ( #2604 #2605 #2606 #2607 #2415 )
- add ability to send engine data to subsequent requests ( #2615 )
- add checker ( #2419 #2476 #2481 #2682 #2682 #2657 )
- by default allow only HTTPS, not HTTP ( #2641 #2659 )
- replace /translations.js with an embedded JSON ( #2660 )
- activate raise_for_error by default ( #2557 )
- don't dump traceback of SearxEngineResponseException on init ( #2635 )

Documentation
~~~~~~~~~~~~~

- update nginx configuration ( #2618 )
- document workaround for using 2 languages simultaneously ( #2479 )
- improve admin-docs about result proxy (morty) configuration ( #2509 )
- fixed typo ( #2457 )

New settings.yml
~~~~~~~~~~~~~~~~

- `general.contact_url` : add link to contact instance maintainer to footer of each page ( #2391 14c7cc0e118f1d0873b32b34793cdec2c5c9c13e #2412 )
- `brand` : move brand options from Makefile to settings.yml ( #2408 #2473 )

Themes
~~~~~~

- oscar: Hide links panel in mobile screens ( #2458 )
- oscar: upgrade dependencies ( #2346 #2673 #2662 )
- remove legacy, courgette and pix-art themes ( #2344 )
- add hyperlink to searx instances list in error message ( #2387 )
- preferences: a tooltip is shown when the mouse is over the engine names ( #2661 )
- Ignore double-quotes when highlighting query parts ( #2553 )
- update autocomplete ( #2593 )

New engines
~~~~~~~~~~~

- ccengine ( #2533 )
- mediathekviewweb ( #2541 )
- solidtorrents ( #2626 )
- solr ( #2652 )
- rumble ( #2588 )
- wiby.me ( #2452 )

Fixed engines
~~~~~~~~~~~~~

- apk_mirror ( #2556 #2642 )
- bing ( #2602 )
- duckduckgo ( #2560 #2559 )
- library genesis ( #2448 )
- ina ( 0ba71c3644c4d20f70528c10eed1385399ec1c82 )
- invidious ( #2451 )
- json_engine ( #2562 )
- google ( #2482 )
- google images ( #2482 )
- google play apps ( 88657fe9c2a41b9be38ee5146e5870672416db12 )
- google play movies ( 50ba2b9e87ef61e96da124f906d3aff4c7870e3f )
- google news ( #2483 #2498 )
- google scholar ( #2611 )
- google video ( #2482 )
- hoogle ( 6255b33c9dcf0d28f0a3307af988565f69259ce2 )
- naver ( #2542 )
- semantic schollar ( f596f5767bed915a5c3bed59ae26283e53f975ca f596f5767bed915a5c3bed59ae26283e53f975ca )
- startpage ( #2396 )
- seznam ( #2564 28286cf3f2308113bf440fb6e7cf326c6ed07889 )
- wikipedia ( #2554 #2565 #2681 #2681 )
- yacy ( #2669 )
- yahoo news ( #2640 #2655 )

Updated engines
~~~~~~~~~~~~~~~

- duckduckgo ( 5f450fda74e80bf350eb1493f66cfa61deaf5cea )
- geektimes ( 45f0e1a859fa12ce2ae0c24dc356922fcad50c8d )
- lobste.rs ( 06b754ad67aa6066aed6df77b5ffb74aabebb040 )
- soundcloud ( #2671 )
- peertube ( #2570 )
- recoll ( #2539 )
- yggtorrent ( #2573 )

Removed engines
~~~~~~~~~~~~~~~

- acgsou ( #2654 )
- google_play_music ( #2558 )
- metager ( #2538 )
- voat ( #2445 )
- yandex ( #2566 )

Bug fixes
~~~~~~~~~

- Fix empty colon in query from selecting Chinese ( #2454 )
- Get correct locale with country from browser ( #2531 )

Code refactoring / reduce the technical debt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- refactor searx.search.SearchQuery and searx.search.EngineRef ( #2398 )
- dynamically set language_support variable ( #2499 )
- engines: add about variable ( #2460 )
- processors ( #2225 5c6a5407a0b124c3323e73c33b81ec1fbd7d2fce )
- remove Fabric file ( #2494 )
- use unittest from py3, remove unittest2 from py2 ( #2608 )

Github
~~~~~~

- add notice for the issue templates ( #2447 )
- every Sunday, call utils/fetch_*.py scripts and create a PR automatically ( #2500 728e09676400221a064627509a31470d8f6e33bf )
- minor change: replace "travis" by "CI" ( #2528 )

Build scripts
~~~~~~~~~~~~~

- update secret key check ( #2411 )
- fix makefile targets `books/{name}.*`  and `books/user.pdf` ( #2420 #2530 )
- upload-pypi-test & linuxdoc has been released on PyPi ( #2456 )
- fix makefile target `gh-pages` : flatten history of branch gh.pages ( #2514 )
- optimize creation of the virtualenv & pyenvinstall targets ( #2421 )
- update pyenv pyenvinstall Make targets ( #2517 )
- makefile.python: remove duplicate pyenv-(un)install targets ( #2418 )
- [fix] make targets engines.languages and useragents.update ( #2643 )
- [fix] utils/serax.sh create_pyenv() - drop duplicate 'pip install .' ( #2621 )

Install scripts
~~~~~~~~~~~~~~~

- drop Ubuntu 16.04 (Xenial Xerus) support ( #2619 )
- replace ubu1910 image by ubu2010 image ( #2435 )
- LXC switch to Fedora 33 / Fedora 31 reached its EOL #2634 (  #2634 )
- add package which to CentOS-7 boilerplate ( #2623 )
- use SEARX_SETTINGS_TEMPLATE from .config environment ( #2417 )
- determine path to makefile.lxc in a LXC ( #2399 )
- remove unused code ( #2401 #2497 )
- support git versions <v2.22 ( #2620 )

Announcement
~~~~~~~~~~~~

We, the searx maintainer team, would like to say a huge thank you for everybody who had been involved in the development of searx or supported us in the past 7 years - making our first stable release available. Special thanks to [NLNet](https://nlnet.nl) for sponsoring multiple features of this release.


0.18.0 2020.12.14
=================

Core
~~~~

- drop Python 2 support ( #2137 #2244 )
- separate index and search routes ( #1681 ). ⚠️ add & remove your searx instance(s) from your browser.
- add external_bang ( #2027 #2043 #2059 )
- add external plugins supports ( #2074 )
- add plugin converting strings into hash digests ( #1246 )
- new category: Onions ( #565 )
- allow searx query parts anywhere in the query ( commit aa3c18dda9329fff875328f6ba97483c417b149a 2aef38c3b9d1fe93e9d665a49b10151d63d92392 )
- preferences: use base_url for prefix of sharing 'currenly saved preferences' (#1249 )
- upgrade to request 2.24.0, pyopenssl is optional ( #2199 )
- force admins to set secret_key if debug mode is disabled ( #2256 )
- standalone searx update ( #1591 )
- architecture clean up ( #2140 #2185 #2195 #2196 #2198 #2189 #2208 #2239 #2241 #2246 #2248 )
- record detail about engine error ( #2332 #2375 #2350 ). Add a new API endpoint: ``/stats/errors``.
- display if an engine does not support HTTPS requests ( #2373 )

New settings.yml
~~~~~~~~~~~~~~~~

- ``use_default_settings``: user settings can relied on the default settings ( #2291 #2362 #2349 )
- ``ui.results_on_new_tab: False`` - for opening result links in a new tab ( #2167 )
- ``ui.advanced_search`` - add preference for displaying advanced settings ( #2327 )
- ``server.method: "POST"`` - Make default query submission method configurable ( #2130 )
- ``server.default_http_headers`` - add default http headers ( #2295 )
- ``engines.*.proxies`` - Using proxy only for specific engines ( #1827 #2319 ), see https://docs.searxng.org/dev/engine_overview.html#settings-yml
- ``enabled_plugins`` - Enabled plugins ( a05c660e3036ad8d02072fc6731af54c2ed6151c )
- ``preferences.lock`` - Let admins lock user preferences ( #2270 )

Oscar theme
~~~~~~~~~~~

- update infobox ( #2131 )

  - Make infoboxes shorter by default.
  - Hide the main image by default as well and set a maximum height even when expanded.
  - Add a toggle at the bottom of the infobox to expand it or to shrink it again.
  - Fix pointhi style
- query suggestion does not keep the language tag of the original query  ( #1314 )
- fix the clear button ( #2306 )

Simple theme
~~~~~~~~~~~~

- Fix autocomplete ( #2205 )

New engines
~~~~~~~~~~~

- ahmia, not_evil ( #565 )
- codeberg ( #2104 )
- command line engines: git grep, find, etc.  ( #2128 #2250 )
- elasticsearch ( #2292 )
- metager ( #2139 )
- naver ( #1912 )
- opensemanticsearch ( #2271 )
- peertube ( #2109 )
- recoll (#2325)
- sepiasearch ( #2227 )

Updated engines
~~~~~~~~~~~~~~~

- digg ( #2285 )
- dbpedia ( #2352 )
- duckduckgo_definitions ( #2224 #2356 )
- duden ( #2359 )
- invidious ( #2116 )
- libgen ( #2360 )
- photon ( #2336 )
- soundclound ( #2365 )
- wikipedia ( #2178 #2363 #2354 )
- wikidata ( #2151 #2224 #2353 ) - faster response time
- yaCy ( #2255 ) - support HTTP digest authentication.
- youtube_noapi ( #2364 )

Fixed engines
~~~~~~~~~~~~~

- 1x ( #2361 )
- answer 'random sha256' ( #2121 )
- bing image ( #1496 )
- duckduckgo ( #2254 )
- genius ( #2371 )
- google ( #2236 )
- google image ( #2115 )
- lobste.rs  ( #2253 )
- piratebay ( #2133 )
- startpage ( #2385 )
- torrentz ( #2101 )

Removed engines
~~~~~~~~~~~~~~~

- filecrop ( #2352 )
- searchcode_doc ( #2372 )
- seedpeer ( #2366 )
- twitter ( #2372 )
- yggtorrent ( #2099 #2375 )

Install scripts & documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- install script & documentation ( #2384 #2380 #2362 #2287 #2283 #2277 #2223 #2211 #2118 #2117 #2063 )

Docker image
~~~~~~~~~~~~

- use Alpine 3.12 ( #1983 )
- uwsgi serves the static files directly. ( #1865 )
- fix k8s support ( #2099 )
- make docker produces clean tag version ( #2182 )

Bug fixes
~~~~~~~~~

- searx.utils.HTMLTextExtractor: invalid HTML don't raise an Exception ( #2190 )
- Fix static URL ( commit da8b227044f45127f705f6ea94a72d368eea73bb )
- Fix autocomplete ( #2127 )
- Fix opensearch.xml ( #2132 #2247 )
- Fix documentation build ( #2237 )
- Some fixes in the fetch languages script ( #2212 )

Special thanks to `NLNet <https://nlnet.nl>`__ for sponsoring multiple features of this release.


0.17.0 2020.07.09
=================

 - New engines

   - eTools
   - Wikibooks
   - Wikinews
   - Wikiquote
   - Wikisource
   - Wiktionary
   - Wikiversity
   - Wikivoyage
   - Rubygems
 - Engine fixes (google, google images, startpage, gigablast, yacy)
 - Private engines introduced - more details: https://docs.searxng.org/blog/private-engines.html
 - Greatly improved documentation - check it at https://docs.searxng.org
 - Added autofocus to all search inputs
 - CSP friendly oscar theme
 - Added option to hide engine errors with `display_error_messages` engine option (true/false values, default is true)
 - Tons of accessibility fixes - see https://github.com/searx/searx/issues/350 for details
 - More flexible branding options: configurable vcs/issue tracker links
 - Added "disable all" & "allow all" options to preferences engine select
 - Autocomplete keyboard navigation fixes
 - Configurable category order
 - Wrap long lines in infoboxes
 - Added RSS subscribtion link
 - Added routing directions to OSM results
 - Added author and length attributes to youtube videos
 - Fixed image stretch with mobile viewport in oscar theme
 - Added translatable JS strings
 - Better HTML annotations - engine names and endpoints are available as classes
 - RTL text fixes in oscar theme
 - Handle weights in accept-language HTTP headers
 - Added answerer results to rss/csv output
 - Added new autocomplete backends to settings.yml
 - Updated opensearch.xml
 - Fixed custom locale setting from settings.yml
 - Translation updates
 - Removed engines: faroo

Special thanks to `NLNet <https://nlnet.nl>`__ for sponsoring multiple features of this release.
Special thanks to https://www.accessibility.nl/english for making accessibilty audit.

News
~~~~

- @HLFH joined the maintainer team
- Dropped Python2 support

0.16.0 2020.01.30
=================

- New engines

  - Splash
  - Apkmirror
  - NPM search
  - Invidious
  - Seedpeer
- New languages

  - Estonian
  - Interlingua
  - Lithuanian
  - Tibetian
  - Occitan
  - Tamil
- Engine fixes (wolframalpha, google scholar, youtube, google images, seznam, google, soundcloud, google cloud, duden, btdigg, google play, bing images, flickr noapi, wikidata, dailymotion, google videos, arxiv, dictzone, fdroid, etymonline, bing, duckduckgo, startpage, voat, 1x, deviantart, digg, gigablast, mojeek, duckduckgo definitions, spotify, libgen, qwant, openstreetmap, wikipedia, ina, microsoft academic, scanr structures)
- Dependency updates
- Speed optimizations
- Initial support for offline engines
- Image format display
- Inline js scripts removed
- Infinite scroll plugin fix
- Simple theme bugfixes
- Docker image updates
- Bang expression fixes
- Result merging fixes
- New environment variable added: SEARXNG_BIND_ADDRESS


News
~~~~

- @return42 joined the maintainer team
- This is the last release with Python2 support

0.15.0 2019.01.06
=================

- New engines

  - Acgsou (files, images, videos, music)
  - Duden.de (general)
  - Seznam (general)
  - Mojeek (general)
- New languages

  - Catalan
  - Welsh
  - Basque
  - Persian (Iran)
  - Galician
  - Dutch (Belgium)
  - Telugu
  - Vietnamese
- New random answerers

  - sha256
  - uuidv4
- New DOI resolsvers

  - sci-hub.tw
- Fix Vim mode on Firefox
- Fix custom select in Oscar theme
- Engine fixes (duckduckgo, google news, currency convert, gigablast, google scholar, wikidata image, etymonline, google videos, startpage, bing image)
- Minor simple theme fixes

- New Youtube icon in Oscar theme
- Get DOI rewriters from settings.yml
- Hide page buttons when infinite scrolling is enabled
- Update user agent versions
- Make Oscar style configurable
- Make suspend times of errored engines configurable

0.14.0 2018.02.19
=================

- New theme: oscar-logicodev dark
- New engines

  - AskSteem (general)
- Autocompleter fix for py3
- Engine fixes (pdbe, pubmed, gigablast, google, yacy, bing videos, microsoft academic)
- "All" option is removed from languages
- Minor UI changes
- Translation updates

0.13.1 2017.11.23
=================

- Bug fixes

  - https://github.com/searx/searx/issues/1088
  - https://github.com/searx/searx/issues/1089

- Dependency updates


0.13.0 2017.11.21
=================

- New theme: simple
- New engines

  - Google videos (video)
  - Bing videos (video)
  - Arxiv (science)
  - OpenAIRE (science)
  - Pubmed (science)
  - Genius (music/lyrics)
- Display engine errors
- Faster startup
- Lots of engine fixes (google images, dictzone, duckduckgo, duckduckgo images, torrentz, faroo, digg, tokyotoshokan, nyaa.si, google news, gitlab, gigablast, geektimes.ru, habrahabr.ru, voat.co, base, json engine, currency convert, google)
- Shorter saved preferences URL
- Fix engine duplications in results
- Py3 compatibility fixes
- Translation updates


0.12.0 2017.06.04
=================

- Python3 compatibility
- New engines

  - 1337x.to (files, music, video)
  - Semantic Scholar (science)
  - Library Genesis (general)
  - Framalibre (IT)
  - Free Software Directory (IT)
- More compact result UI (oscar theme)
- Configurable static content and template path
- Spelling suggestions
- Multiple engine fixes (duckduckgo, bing, swisscows, yahoo news, bing news, twitter, bing images)
- Reduced static image size
- Docker updates
- Translation updates


Special thanks to `NLNet <https://nlnet.nl>`__ for sponsoring multiple features of this release.


0.11.0 2017.01.10
=================

- New engines

  - Protein Data Bank Europe (science)
  - Voat.co (general, social media)
  - Online Etimology Dictionary (science)
  - CCC tv (video, it)
  - Searx (all categories - can rotate multiple other instances)
- Answerer functionality (see answerer section on /preferences)
- Local answerers

  - Statistical functions
  - Random value generator
- Result proxy support (with `morty <https://github.com/asciimoo/morty>`__)
- Extended time range filter
- Improved search language support
- Multiple engine fixes (digbt, 500px, google news, ixquick, bing, kickass, google play movies, habrahabr, yandex)
- Minor UI improvements
- Suggestion support for JSON engine
- Result and query escaping fixes
- Configurable HTTP server version
- More robust search error handling
- Faster webapp initialization in debug mode
- Search module refactor
- Translation updates


0.10.0 2016.09.06
=================

- New engines

  - Archive.is (general)
  - INA (videos)
  - Scanr (science)
  - Google Scholar (science)
  - Crossref (science)
  - Openrepos (files)
  - Microsoft Academic Search Engine (science)
  - Hoogle (it)
  - Diggbt (files)
  - Dictzone (general - dictionary)
  - Translated (general - translation)
- New Plugins

  - Infinite scroll on results page
  - DOAI rewrite
- Full theme redesign
- Display the number of results
- Filter searches by date range
- Instance config API endpoint
- Dependency version updates
- Socks proxy support for outgoing requests
- 404 page


News
~~~~

@kvch joined the maintainer team


0.9.0 2016.05.24
================

- New search category: science
- New engines

  - Wolframalpha (science)
  - Frinkiac (images)
  - Arch Linux (it)
  - BASE - Bielefeld Academic Search Engine (science)
  - Dokuwiki (general)
  - Nyaa.se (files, images, music, video)
  - Reddit (general, images, news, social media)
  - Torrentz.eu (files, music, video)
  - Tokyo Toshokan (files, music, video)
  - F-Droid (files)
  - Erowid (general)
  - Bitbucket (it)
  - GitLab (it)
  - Geektimes (it)
  - Habrahabr (it)
- New plugins

  - Open links in new tab
  - Vim hotkeys for better navigation
- Wikipedia/Mediawiki engine improvements
- Configurable instance name
- Configurable connection pool size
- Fixed broken google engine
- Better docker image
- Images in standard results
- Fixed and refactored user settings (Warning: backward incompatibility - you have to reset your custom engine preferences)
- Suspending engines on errors
- Simplified development/deployment tooling
- Translation updates
- Multilingual autocompleter
- Qwant autocompleter backend


0.8.1 2015.12.22
================

- More efficient result parsing
- Rewritten google engine to prevent app crashes
- Other engine fixes/tweaks

  - Bing news
  - Btdigg
  - Gigablast
  - Google images
  - Startpage


News
~~~~

New documentation page is available: https://docs.searxng.org


0.8.0 2015.09.08
================

- New engines

  - Blekko (image)
  - Gigablast (general)
  - Spotify (music)
  - Swisscows (general, images)
  - Qwant (general, images, news, social media)
- Plugin system
- New plugins

  - HTTPS rewrite
  - Search on cagetory select
  - User information
  - Tracker url part remover
- Multiple outgoing IP and HTTP/HTTPS proxy support
- New autocompleter: startpage
- New theme: pix-art
- Settings file structure change
- Fabfile, docker deployment
- Optional safesearch result filter
- Force HTTPS in engines if possible
- Disabled HTTP referrer on outgoing links
- Display cookie information
- Prettier search URLs
- Right-to-left text handling in themes
- Translation updates (New locales: Chinese, Hebrew, Portuguese, Romanian)


New dependencies
~~~~~~~~~~~~~~~~

- pyopenssl
- ndg-httpsclient
- pyasn1
- pyasn1-modules
- certifi


News
~~~~

@dalf joined the maintainer "team"


0.7.0 2015.02.03
================

- New engines

  - Digg
  - Google Play Store
  - Deezer
  - Btdigg
  - Mixcloud
  - 1px
- Image proxy
- Search speed improvements
- Autocompletition of engines, shortcuts and supported languages
- Translation updates (New locales: Turkish, Russian)
- Default theme changed to oscar
- Settings option to disable engines by default
- UI code cleanup and restructure
- Engine tests
- Multiple engine bug fixes and tweaks
- Config option to set default interface locale
- Flexible result template handling
- Application logging and sophisticated engine exception tracebacks
- Kickass torrent size display (oscar theme)


New dependencies
~~~~~~~~~~~~~~~~

-  pygments - http://pygments.org/


0.6.0 - 2014.12.25
==================

- Changelog added
- New engines

  - Flickr (api)
  - Subtitleseeker
  - photon
  - 500px
  - Searchcode
  - Searchcode doc
  - Kickass torrent
- Precise search request timeout handling
- Better favicon support
- Stricter config parsing
- Translation updates
- Multiple ui fixes
- Flickr (noapi) engine fix
- Pep8 fixes


News
~~~~

Health status of searx instances and engines: http://stats.searx.oe5tpo.com
(source: https://github.com/pointhi/searx_stats)
