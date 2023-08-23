.. _settings search:

===========
``search:``
===========

.. code:: yaml

   search:
     safe_search: 0
     autocomplete: ""
     default_lang: ""
     ban_time_on_fail: 5
     max_ban_time_on_fail: 120
     suspended_times:
       SearxEngineAccessDenied: 86400
       SearxEngineCaptcha: 86400
       SearxEngineTooManyRequests: 3600
       cf_SearxEngineCaptcha: 1296000
       cf_SearxEngineAccessDenied: 86400
       recaptcha_SearxEngineCaptcha: 604800
     formats:
       - html

``safe_search``:
  Filter results.

  - ``0``: None
  - ``1``: Moderate
  - ``2``: Strict

``autocomplete``:
  Existing autocomplete backends, leave blank to turn it off.

  - ``dbpedia``
  - ``duckduckgo``
  - ``google``
  - ``mwmbl``
  - ``startpage``
  - ``swisscows``
  - ``qwant``
  - ``wikipedia``

``default_lang``:
  Default search language - leave blank to detect from browser information or
  use codes from :origin:`searx/languages.py`.

``languages``:
  List of available languages - leave unset to use all codes from
  :origin:`searx/languages.py`.  Otherwise list codes of available languages.
  The ``all`` value is shown as the ``Default language`` in the user interface
  (in most cases, it is meant to send the query without a language parameter ;
  in some cases, it means the English language) Example:

  .. code:: yaml

     languages:
       - all
       - en
       - en-US
       - de
       - it-IT
       - fr
       - fr-BE

``ban_time_on_fail``:
  Ban time in seconds after engine errors.

``max_ban_time_on_fail``:
  Max ban time in seconds after engine errors.

``suspended_times``:
  Engine suspension time after error (in seconds; set to 0 to disable)

  ``SearxEngineAccessDenied``: 86400
    For error "Access denied" and "HTTP error [402, 403]"

  ``SearxEngineCaptcha``: 86400
    For error "CAPTCHA"

  ``SearxEngineTooManyRequests``: 3600
    For error "Too many request" and "HTTP error 429"

  Cloudflare CAPTCHA:
     - ``cf_SearxEngineCaptcha``: 1296000
     - ``cf_SearxEngineAccessDenied``: 86400

  Google CAPTCHA:
    - ``recaptcha_SearxEngineCaptcha``: 604800

``formats``:
  Result formats available from web, remove format to deny access (use lower
  case).

  - ``html``
  - ``csv``
  - ``json``
  - ``rss``
