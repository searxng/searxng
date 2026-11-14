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

.. _settings general.contact_url:

``contact_url`` : ``$SEARXNG_CONTACT_URL``
  Contact ``mailto:`` address or WEB form.

  .. attention::

     In order to comply with the policy of Wikidata and other services SearXNG
     uses, the ``contact_url`` is required!

     - :py:obj:`searx.utils.searxng_useragent`
     - :py:obj:`searx.wikidata.get_wikidata_headers`

``enable_metrics``:
  Enabled by default. Record various anonymous metrics available at ``/stats``,
  ``/stats/errors`` and ``/preferences``.

``open_metrics``:
  Disabled by default. Set to a secret password to expose an
  `OpenMetrics API <https://github.com/prometheus/OpenMetrics>`_ at ``/metrics``,
  e.g. for usage with Prometheus. The ``/metrics`` endpoint is using HTTP Basic Auth,
  where the password is the value of ``open_metrics`` set above. The username used for
  Basic Auth can be randomly chosen as only the password is being validated.
