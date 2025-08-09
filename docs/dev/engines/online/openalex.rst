.. _openalex engine:

=========
OpenAlex
=========

Overview
========

The OpenAlex engine integrates the `OpenAlex`_ Works API to return scientific paper
results using the :origin:`paper.html <searx/templates/simple/result_templates/paper.html>`
template. It is an "online" JSON engine that uses the official public API and does
not require an API key.

.. _OpenAlex: https://openalex.org
.. _OpenAlex API overview: https://docs.openalex.org/how-to-use-the-api/api-overview

Key features
------------

- Uses the official Works endpoint (JSON)
- Paging support via ``page`` and ``per-page``
- Relevance sorting (``sort=relevance_score:desc``)
- Language filter support (maps SearXNG language to ``filter=language:<iso2>``)
- Maps fields commonly used in scholarly results: title, authors, abstract
  (reconstructed from inverted index), journal/venue, publisher, DOI, tags
  (concepts), PDF/HTML links, pages, volume, issue, published date, and a short
  citations comment
- Supports OpenAlex "polite pool" by adding a ``mailto`` parameter


Configuration
=============

Minimal example for :origin:`settings.yml <searx/settings.yml>`:

.. code:: yaml

   - name: openalex
     engine: openalex
     shortcut: oa
     categories: science, scientific publications
     timeout: 5.0
     # Recommended by OpenAlex: join the polite pool with an email address
     mailto: "[email protected]"

Notes
-----

- The ``mailto`` key is optional but recommended by OpenAlex for better service.
- Language is inherited from the user's UI language; when it is not ``all``, the
  engine adds ``filter=language:<iso2>`` (e.g. ``language:fr``). If OpenAlex has
  few results for that language, you may see fewer items.
- Results typically include a main link. When the primary landing page from
  OpenAlex is a DOI resolver, the engine will use that stable link. When an open
  access link is available, it is exposed via the ``PDF`` and/or ``HTML`` links
  in the result footer.


What is returned
================

Each result uses the ``paper.html`` template and may include:

- ``title`` and ``content`` (abstract; reconstructed from the inverted index)
- ``authors`` (display names)
- ``journal`` (host venue display name) and ``publisher``
- ``doi`` (normalized to the plain DOI, without the ``https://doi.org/`` prefix)
- ``tags`` (OpenAlex concepts display names)
- ``pdf_url`` (Open access PDF if available) and ``html_url`` (landing page)
- ``publishedDate`` (parsed from ``publication_date``)
- ``pages``, ``volume``, ``number`` (issue)
- ``type`` and a brief ``comments`` string with citation count


Rate limits & polite pool
=========================

OpenAlex offers a free public API with generous daily limits. For extra courtesy
and improved service quality, include a contact email in each request via
``mailto``. You can set it directly in the engine configuration as shown above.
See: `OpenAlex API overview`_.


Troubleshooting
===============

- Few or no results in a non-English UI language:
  Ensure the selected language has sufficient coverage at OpenAlex, or set the
  UI language to English and retry.
- Preference changes fail while testing locally:
  Make sure your ``server.secret_key`` and ``server.base_url`` are set in your
  instance settings so signed cookies work; see :ref:`settings server`.


Implementation
===============

.. automodule:: searx.engines.openalex
   :members:
