.. SPDX-License-Identifier: AGPL-3.0-or-later

----

.. figure:: https://raw.githubusercontent.com/searxng/searxng/master/src/brand/searxng.svg
   :target: https://docs.searxng.org/
   :alt: SearXNG
   :width: 100%
   :align: center

----

Privacy-respecting, hackable `metasearch engine`_

Searx.space_ lists ready-to-use running instances.

A user_, admin_ and developer_ handbook is available on the homepage_.

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

.. |weblate| image:: https://translate.codeberg.org/widgets/searxng/-/searxng/svg-badge.svg
   :target: https://translate.codeberg.org/projects/searxng/


Contact
=======

Ask questions or just chat about SearXNG on

IRC
  `#searxng on libera.chat <https://web.libera.chat/?channel=#searxng>`_
  which is bridged to Matrix.

Matrix
  `#searxng:matrix.org <https://matrix.to/#/#searxng:matrix.org>`_

Differences to searx
====================

SearXNG is a fork of `searx`_, with notable changes:

.. _searx: https://github.com/searx/searx


User experience
---------------

- Reworked (and still simple) theme:

  * Usable on desktop, tablet and mobile.
  * Light and dark versions (available in the preferences).
  * Right-to-left language support.
  * `Screenshots <https://dev.searxng.org/screenshots.html>`_

- The translations are up to date, you can contribute on `Weblate`_
- The preferences page has been updated:

  * Browse which engines are reliable or not.
  * Engines are grouped inside each tab.
  * Each engine has a description.

- Thanks to the anonymous metrics, it is easier to report malfunctioning engines,
  so they get fixed quicker

  - `Turn off metrics on the server
    <https://docs.searxng.org/admin/engines/settings.html#general>`_ if you don't want them recorded.

- Administrators can `block and/or replace the URLs in the search results
  <https://github.com/searxng/searxng/blob/5c1c0817c3996c5670a545d05831d234d21e6217/searx/settings.yml#L191-L199>`_


Setup
-----

- No need for `Morty`_ to proxy images, even on a public instance.
- No need for `Filtron`_ to block bots, as there is now a built-in `limiter`_.
- A well maintained `Docker image`_, now also built for ARM64 and ARM/v7 architectures.
  (Alternatively there are up to date installation scripts.)

.. _Docker image: https://github.com/searxng/searxng-docker


Contributing
------------

- Readable debug log.
- Contributing is easier, thanks to the `Development Quickstart`_ guide.
- A lot of code cleanup and bugfixes.
- Up to date list dependencies.

.. _Morty: https://github.com/asciimoo/morty
.. _Filtron: https://github.com/searxng/filtron
.. _limiter: https://docs.searxng.org/src/searx.plugins.limiter.html
.. _Weblate: https://translate.codeberg.org/projects/searxng/searxng/
.. _Development Quickstart: https://docs.searxng.org/dev/quickstart.html


Translations
============

Help translate SearXNG at `Weblate`_

.. figure:: https://translate.codeberg.org/widgets/searxng/-/multi-auto.svg
   :target: https://translate.codeberg.org/projects/searxng/


Codespaces
==========

You can contribute from your browser using `GitHub Codespaces`_:

- Fork the repository
- Click on the ``<> Code`` green button
- Click on the ``Codespaces`` tab instead of ``Local``
- Click on ``Create codespace on master``
- VSCode is going to start in the browser
- Wait for ``git pull && make install`` to appears and then to disapear
- You have `120 hours per month`_ (see also your `list of existing Codespaces`_)
- You can start SearXNG using ``make run`` in the terminal or by pressing ``Ctrl+Shift+B``.

.. _GitHub Codespaces: https://docs.github.com/en/codespaces/overview
.. _120 hours per month: https://github.com/settings/billing
.. _list of existing Codespaces: https://github.com/codespaces
