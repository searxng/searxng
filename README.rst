.. SPDX-License-Identifier: AGPL-3.0-or-later

.. _metasearch engine: https://en.wikipedia.org/wiki/Metasearch_engine
.. _Installation guide: https://docs.searxng.org/admin/installation.html
.. _Configuration guide: https://docs.searxng.org/admin/settings/index.html
.. _CONTRIBUTING: https://github.com/searxng/searxng/blob/master/CONTRIBUTING.rst
.. _LICENSE: https://github.com/searxng/searxng/blob/master/LICENSE

.. figure:: https://raw.githubusercontent.com/searxng/searxng/master/client/simple/src/brand/searxng.svg
   :target: https://searxng.org
   :alt: SearXNG
   :width: 512px


SearXNG is a `metasearch engine`_. Users are neither tracked nor profiled.

.. image:: https://img.shields.io/badge/organization-3050ff?style=flat-square&logo=searxng&logoColor=fff&cacheSeconds=86400
   :target: https://github.com/searxng
   :alt: Organization

.. image:: https://img.shields.io/badge/documentation-3050ff?style=flat-square&logo=readthedocs&logoColor=fff&cacheSeconds=86400
   :target: https://docs.searxng.org
   :alt: Documentation

.. image:: https://img.shields.io/github/license/searxng/searxng?style=flat-square&label=license&color=3050ff&cacheSeconds=86400
   :target: https://github.com/searxng/searxng/blob/master/LICENSE
   :alt: License

.. image:: https://img.shields.io/github/commit-activity/y/searxng/searxng/master?style=flat-square&label=commits&color=3050ff&cacheSeconds=3600
   :target: https://github.com/searxng/searxng/commits/master/
   :alt: Commits

.. image:: https://img.shields.io/weblate/progress/searxng?server=https%3A%2F%2Ftranslate.codeberg.org&style=flat-square&label=translated&color=3050ff&cacheSeconds=86400
   :target: https://translate.codeberg.org/projects/searxng/
   :alt: Translated

Setup
=====

To install SearXNG, see `Installation guide`_.

To fine-tune SearXNG, see `Configuration guide`_.

Further information on *how-to* can be found `here <https://docs.searxng.org/admin/index.html>`_.

Connect
=======

If you have questions or want to connect with others in the community:

- `#searxng:matrix.org <https://matrix.to/#/#searxng:matrix.org>`_

Contributing
============

See CONTRIBUTING_ for more details.

License
=======

This project is licensed under the GNU Affero General Public License (AGPL-3.0).
See LICENSE_ for more details.



.. _nova-nodes-mcp:

NovaNodes MCP Gateway Integration
==================================

The `NovaNodes MCP Gateway <https://github.com/TheNovaNodes/nova-searxng-mcp>`_ provides a bridge between SearXNG and AI agents using the Model Context Protocol (MCP).

Why use it?
-----------

* **Private search for AI agents** — route MCP search calls through your own SearXNG instance, no third-party APIs, no tracking
* **90+ engines** — Bing, Brave, DuckDuckGo, Google, Startpage, Qwant, and more
* **Zero configuration** — just point SEARXNG_URL to your local SearXNG instance
* **MCP native** — compatible with Claude Desktop, Continue, and any MCP client

Quick start
~~~~~~~~~~~

.. code-block:: bash

    pip install nova-searxng-mcp
    # In your .env: SEARXNG_URL=http://127.0.0.1:8080
    python -m searxng_gateway.server

See the `repository <https://github.com/TheNovaNodes/nova-searxng-mcp>`_ for full documentation.

Compatible with
~~~~~~~~~~~~~~~

* `AnythingLLM <https://github.com/Mintplex-Labs/anything-llm>`_ — use SearXNG as private search backend for agent web-browsing
* `OpenClaw <https://github.com/TheNovaNodes>`_ — multi-agent orchestration with private search and memory
