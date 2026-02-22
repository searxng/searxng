=================
Local Search APIs
=================

.. sidebar:: further read

   - `Comparison to alternatives
     <https://docs.meilisearch.com/learn/what_is_meilisearch/comparison_to_alternatives.html>`_

.. contents::
   :depth: 1
   :local:
   :backlinks: entry

.. sidebar:: info

   Initial sponsored by `Search and Discovery Fund
   <https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.

Administrators might find themselves wanting to integrate locally running search
engines.  The following ones are supported for now:

* `Elasticsearch`_
* `Meilisearch`_
* `Solr`_

Each search engine is powerful, capable of full-text search.  All of the engines
above are added to ``settings.yml`` just commented out, as you have to
``base_url`` for all them.

Please note that if you are not using HTTPS to access these engines, you have to
enable HTTP requests by setting ``enable_http`` to ``True``.

Furthermore, if you do not want to expose these engines on a public instance,
you can still add them and limit the access by setting ``tokens`` as described
in section :ref:`private engines`.

.. _engine meilisearch:

MeiliSearch
===========

.. automodule:: searx.engines.meilisearch
  :members:


.. _engine elasticsearch:

Elasticsearch
=============

.. automodule:: searx.engines.elasticsearch
  :members:

.. _engine solr:

Solr
====

.. automodule:: searx.engines.solr
  :members:

