==================
Google API Engines
==================

.. contents:: Contents
   :depth: 2
   :local:
   :backlinks: entry

These engines provide Google result types through third-party JSON SERP APIs.
They share the same engine semantics and differ only by the configured
provider (currently ``serpbase`` or ``serper``).

- ``serpbase``: https://serpbase.dev / https://serpbase.dev/docs
- ``serper``: https://serper.dev

Both providers are intended to be low-cost Google SERP API options.

They are optional additions to the existing Google engines.  Enabling
``google_api``, ``google_images_api``, ``google_news_api`` or
``google_videos_api`` does not replace ``google``, ``google_images``,
``google_news`` or ``google_videos``.


Configuration
-------------

These engines are configured in :origin:`searx/settings.yml` with
``inactive: true`` by default, because they require an API key.

Example configuration::

  - name: google api
    engine: google_api
    provider: serpbase
    api_key: "your-api-key"
    shortcut: goapi
    inactive: false

  - name: google images api
    engine: google_images_api
    provider: serpbase
    api_key: "your-api-key"
    shortcut: goiapi
    inactive: false

Set ``provider`` to ``serper`` to use that backend instead.

.. _google_api engine:

Google API
----------

.. automodule:: searx.engines.google_api
   :members:

.. _google_images_api engine:

Google Images API
-----------------

.. automodule:: searx.engines.google_images_api
   :members:

.. _google_news_api engine:

Google News API
---------------

.. automodule:: searx.engines.google_news_api
   :members:

.. _google_videos_api engine:

Google Videos API
-----------------

.. automodule:: searx.engines.google_videos_api
   :members:

.. automodule:: searx.engines.google_api_providers
   :members:
