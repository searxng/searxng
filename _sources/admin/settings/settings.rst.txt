.. _settings.yml:

================
``settings.yml``
================

This page describe the options possibilities of the :origin:`searx/settings.yml`
file.

.. sidebar:: Further reading ..

   - :ref:`use_default_settings.yml`
   - :ref:`search API`

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

.. _settings location:

settings.yml location
=====================

The initial ``settings.yml`` we be load from these locations:

1. the full path specified in the ``SEARXNG_SETTINGS_PATH`` environment variable.
2. ``/etc/searxng/settings.yml``

If these files don't exist (or are empty or can't be read), SearXNG uses the
:origin:`searx/settings.yml` file.  Read :ref:`settings use_default_settings` to
see how you can simplify your *user defined* ``settings.yml``.



.. _settings use_default_settings:

use_default_settings
====================

.. sidebar:: ``use_default_settings: true``

   - :ref:`settings location`
   - :ref:`use_default_settings.yml`
   - :origin:`/etc/searxng/settings.yml <utils/templates/etc/searxng/settings.yml>`

The user defined ``settings.yml`` is loaded from the :ref:`settings location`
and can relied on the default configuration :origin:`searx/settings.yml` using:

 ``use_default_settings: true``

``server:``
  In the following example, the actual settings are the default settings defined
  in :origin:`searx/settings.yml` with the exception of the ``secret_key`` and
  the ``bind_address``:

  .. code:: yaml

    use_default_settings: true
    server:
        secret_key: "ultrasecretkey"   # change this!
        bind_address: "[::]"

``engines:``
  With ``use_default_settings: true``, each settings can be override in a
  similar way, the ``engines`` section is merged according to the engine
  ``name``.  In this example, SearXNG will load all the default engines, will
  enable the ``bing`` engine and define a :ref:`token <private engines>` for
  the arch linux engine:

  .. code:: yaml

    use_default_settings: true
    server:
      secret_key: "ultrasecretkey"   # change this!
    engines:
      - name: arch linux wiki
        tokens: ['$ecretValue']
      - name: bing
        disabled: false


``engines:`` / ``remove:``
  It is possible to remove some engines from the default settings. The following
  example is similar to the above one, but SearXNG doesn't load the the google
  engine:

  .. code:: yaml

    use_default_settings:
      engines:
        remove:
          - google
    server:
      secret_key: "ultrasecretkey"   # change this!
    engines:
      - name: arch linux wiki
        tokens: ['$ecretValue']

``engines:`` / ``keep_only:``
  As an alternative, it is possible to specify the engines to keep. In the
  following example, SearXNG has only two engines:

  .. code:: yaml

    use_default_settings:
      engines:
        keep_only:
          - google
          - duckduckgo
    server:
      secret_key: "ultrasecretkey"   # change this!
    engines:
      - name: google
        tokens: ['$ecretValue']
      - name: duckduckgo
        tokens: ['$ecretValue']
