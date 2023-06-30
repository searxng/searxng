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

``debug`` : ``$SEARXNG_DEBUG``
  Allow a more detailed log if you run SearXNG directly. Display *detailed* error
  messages in the browser too, so this must be deactivated in production.

``donation_url`` :
  Set value to ``true`` to use your own donation page written in the
  :ref:`searx/info/en/donate.md <searx.infopage>` and use ``false`` to disable
  the donation link altogether.

``privacypolicy_url``:
  Link to privacy policy.

``contact_url``:
  Contact ``mailto:`` address or WEB form.

``enable_metrics``:
  Enabled by default. Record various anonymous metrics availabled at ``/stats``,
  ``/stats/errors`` and ``/preferences``.
