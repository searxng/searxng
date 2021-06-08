====================
Local Search Engines
====================

.. sidebar:: further read

   - `Comparison to alternatives
     <https://docs.meilisearch.com/learn/what_is_meilisearch/comparison_to_alternatives.html>`_

Administrators might find themselves wanting to integrate locally running search
engines.  The following ones are supported for now:

* `Elasticsearch`_
* `Meilisearch`_
* `Solr`_

Each search engine is powerful, capable of full-text search.  All of the engines
above are added to ``settings.yml`` just commented out, as you have to
``base_url`` for all them.

Please note that if you are not using HTTPS to access these engines, you have to enable
HTTP requests by setting ``enable_http`` to ``True``.

Futhermore, if you do not want to expose these engines on a public instance, you
can still add them and limit the access by setting ``tokens`` as described in
section :ref:`private engines`.

.. _engine meilisearch:

MeiliSearch
===========

.. sidebar:: info

   - :origin:`meilisearch.py <searx/engines/meilisearch.py>`
   - `MeiliSearch <https://www.meilisearch.com>`_
   - `MeiliSearch Documentation <https://docs.meilisearch.com/>`_
   - `Install MeiliSearch
     <https://docs.meilisearch.com/learn/getting_started/installation.html>`_

MeiliSearch_ is aimed at individuals and small companies.  It is designed for
small-scale (less than 10 million documents) data collections.  E.g. it is great
for storing web pages you have visited and searching in the contents later.

The engine supports faceted search, so you can search in a subset of documents
of the collection.  Furthermore, you can search in MeiliSearch_ instances that
require authentication by setting ``auth_token``.

Here is a simple example to query a Meilisearch instance:

.. code:: yaml

  - name: meilisearch
    engine: meilisearch
    shortcut: mes
    base_url: http://localhost:7700
    index: my-index
    enable_http: true


.. _engine elasticsearch:

Elasticsearch
=============

.. sidebar:: info

   - :origin:`elasticsearch.py <searx/engines/elasticsearch.py>`
   - `Elasticsearch <https://www.elastic.co/elasticsearch/>`_
   - `Elasticsearch Guide
     <https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html>`_
   - `Install Elasticsearch
     <https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html>`_

Elasticsearch_ supports numerous ways to query the data it is storing.  At the
moment the engine supports the most popular search methods (``query_type``):

- ``match``,
- ``simple_query_string``,
- ``term`` and
- ``terms``.

If none of the methods fit your use case, you can select ``custom`` query type
and provide the JSON payload to submit to Elasticsearch in
``custom_query_json``.

The following is an example configuration for an Elasticsearch_ instance with
authentication configured to read from ``my-index`` index.

.. code:: yaml

  - name: elasticsearch
    shortcut: es
    engine: elasticsearch
    base_url: http://localhost:9200
    username: elastic
    password: changeme
    index: my-index
    query_type: match
    # custom_query_json: '{ ... }'
    enable_http: true

.. _engine solr:

Solr
====

.. sidebar:: info

   - :origin:`solr.py <searx/engines/solr.py>`
   - `Solr <https://solr.apache.org>`_
   - `Solr Resources <https://solr.apache.org/resources.html>`_
   - `Install Solr <https://solr.apache.org/guide/installing-solr.html>`_

Solr_ is a popular search engine based on Lucene, just like Elasticsearch_.  But
instead of searching in indices, you can search in collections.

This is an example configuration for searching in the collection
``my-collection`` and get the results in ascending order.

.. code:: yaml

  - name: solr
    engine: solr
    shortcut: slr
    base_url: http://localhost:8983
    collection: my-collection
    sort: asc
    enable_http: true


Acknowledgment
==============

This development was sponsored by `Search and Discovery Fund
<https://nlnet.nl/discovery>`_ of `NLnet Foundation <https://nlnet.nl/>`_.
