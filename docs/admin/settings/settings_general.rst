.. _settings general:

============
``general:``
============

.. code:: yaml

   general:
     debug: false
     instance_name:  "SearXNG"
     privacypolicy_url: false
     donation_url: false
     contact_url: false
     enable_metrics: true
     open_metrics: ''

``debug`` : ``$SEARXNG_DEBUG``
  In debug mode, the server provides an interactive debugger, will reload when
  code is changed and activates a verbose logging.

  .. attention::

     The debug setting is intended for local development server.  Don't
     activate debug (don't use a development server) when deploying to
     production.

``donation_url`` :
  Set value to ``true`` to use your own donation page written in the
  :ref:`searx/info/en/donate.md <searx.infopage>` and use ``false`` to disable
  the donation link altogether.

``privacypolicy_url``:
  Link to privacy policy.

``contact_url``:
  Contact ``mailto:`` address or WEB form.

``enable_metrics``:
  Enabled by default. Record various anonymous metrics available at ``/stats``,
  ``/stats/errors`` and ``/preferences``.

``open_metrics``:
  Disabled by default. Set to a secret password to expose an
  `OpenMetrics API <https://github.com/prometheus/OpenMetrics>`_ at ``/metrics``,
  e.g. for usage with Prometheus. The ``/metrics`` endpoint is using HTTP Basic Auth,
  where the password is the value of ``open_metrics`` set above. The username used for
  Basic Auth can be randomly chosen as only the password is being validated.

  Per-engine request counters use the ``engine_name`` label. In addition to
  ``searxng_engines_request_count_total``, SearXNG exports
  ``searxng_engines_successful_request_count_total`` and
  ``searxng_engines_error_request_count_total``. A successful request includes a
  valid response with no results; an error request is one handled by the engine
  processor's exception path. These counters describe requests sent to upstream
  engines, not incoming ``/search`` requests.
