.. SPDX-License-Identifier: AGPL-3.0-or-later

----

.. figure:: https://raw.githubusercontent.com/searxng/searxng/master/src/brand/searxng.svg
   :target: https://docs.searxng.org/
   :alt: SearXNG
   :width: 100%
   :align: center

----

Privacy-respecting, hackable `metasearch engine`_

If you are looking for running instances, ready to use, then visit searx.space_.
Otherwise jump to the user_, admin_ and developer_ handbooks you will find on
our homepage_.

|SearXNG install|
|SearXNG homepage|
|SearXNG wiki|
|AGPL License|
|Issues|
|commits|
|weblate|
|SearXNG logo|

----

.. _searx.space: https://searx.space
.. _user: https://docs.searxng.org/user
.. _admin: https://docs.searxng.org/admin
.. _developer: https://docs.searxng.org/dev
.. _homepage: https://docs.searxng.org/
.. _metasearch engine: https://en.wikipedia.org/wiki/Metasearch_engine

.. |SearXNG logo| image:: https://raw.githubusercontent.com/searxng/searxng/master/src/brand/searxng-wordmark.svg
   :target: https://docs.searxng.org/
   :width: 5%

.. |SearXNG install| image:: https://img.shields.io/badge/-install-blue
   :target: https://docs.searxng.org/admin/installation.html

.. |SearXNG homepage| image:: https://img.shields.io/badge/-homepage-blue
   :target: https://docs.searxng.org/

.. |SearXNG wiki| image:: https://img.shields.io/badge/-wiki-blue
   :target: https://github.com/searxng/searxng/wiki

.. |AGPL License|  image:: https://img.shields.io/badge/license-AGPL-blue.svg
   :target: https://github.com/searxng/searxng/blob/master/LICENSE

.. |Issues| image:: https://img.shields.io/github/issues/searxng/searxng?color=yellow&label=issues
   :target: https://github.com/searxng/searxng/issues

.. |PR| image:: https://img.shields.io/github/issues-pr-raw/searxng/searxng?color=yellow&label=PR
   :target: https://github.com/searxng/searxng/pulls

.. |commits| image:: https://img.shields.io/github/commit-activity/y/searxng/searxng?color=yellow&label=commits
   :target: https://github.com/searxng/searxng/commits/master

.. |weblate| image:: https://weblate.bubu1.eu/widgets/searxng/-/searxng/svg-badge.svg
   :target: https://weblate.bubu1.eu/projects/searxng/


Contact
=======

Come join us if you have questions or just want to chat about SearXNG.

Matrix
  `#searxng:matrix.org <https://matrix.to/#/#searxng:matrix.org>`_

IRC
  `#searxng on libera.chat <https://web.libera.chat/?channel=#searxng>`_
  which is bridged to Matrix.


Differences to searx
====================

SearXNG is a fork of `searx`_.  Here are some of the changes:

.. _searx: https://github.com/searx/searx


User experience
---------------

- Huge update of the simple theme:

  * usable on desktop, tablet and mobile
  * light and dark versions (you can choose in the preferences)
  * support right-to-left languages
  * `see the screenshots <https://dev.searxng.org/screenshots.html>`_

- the translations are up to date, you can contribute on `Weblate`_
- the preferences page has been updated:

  * you can see which engines are reliable or not
  * engines are grouped inside each tab
  * each engine has a description

- it is easier to report a bug of an engine
- but you can also disable the recording of the metrics on the server


Setup
-----

- the Docker image is now also built for ARM64 and ARM/v7 architectures
- you don't need `Morty`_ to proxy the images even on a public instance
- on the way to embed `Filtron`_ into SearXNG
- up to date installation scripts


Contributing is easier
----------------------

- readable debug log
- contributions to the themes are made easier, check out our `Development
  Quickstart`_ guide
- a lot of code cleanup and bug fixes
- the dependencies are up to date

.. _Morty: https://github.com/asciimoo/morty
.. _Filtron: https://github.com/searxng/filtron
.. _Weblate: https://weblate.bubu1.eu/projects/searxng/searxng/
.. _Development Quickstart: https://docs.searxng.org/dev/quickstart.html


Translations
============

We need translators, suggestions are welcome at
https://weblate.bubu1.eu/projects/searxng/searxng/

.. figure:: https://weblate.bubu1.eu/widgets/searxng/-/multi-auto.svg
   :target: https://weblate.bubu1.eu/projects/searxng/


Make a donation
===============

You can support the SearXNG project by clicking on the donation page: `https://docs.searxng.org/donate.html <https://docs.searxng.org/donate.html>`_
