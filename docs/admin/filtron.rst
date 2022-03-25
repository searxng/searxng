
.. _searxng filtron:

==========================
How to protect an instance
==========================

.. tip::

   To protect your instance a installation of filtron (as described here) is no
   longer needed, alternatively activate the :ref:`limiter plugin` in your
   ``settings.yml``. Note that the :ref:`limiter plugin` requires a :ref:`Redis
   <settings redis>` database.


.. sidebar:: further reading

   - :ref:`filtron.sh`
   - :ref:`nginx searxng site`

.. _filtron: https://github.com/searxng/filtron

SearXNG depends on external search services.  To avoid the abuse of these services
it is advised to limit the number of requests processed by SearXNG.

An application firewall, filtron_ solves exactly this problem.  Filtron is just
a middleware between your web server (nginx, apache, ...) and searx, we describe
such infrastructures in chapter: :ref:`architecture`.


filtron & go
============

.. _Go: https://golang.org/
.. _filtron README: https://github.com/searxng/filtron/blob/master/README.md

Filtron needs Go_ installed.  If Go_ is preinstalled, filtron_ is simply
installed by ``go get`` package management (see `filtron README`_).  If you use
filtron as middleware, a more isolated setup is recommended.  To simplify such
an installation and the maintenance of, use our script :ref:`filtron.sh`.

.. _Sample configuration of filtron:

Sample configuration of filtron
===============================

.. sidebar:: Tooling box

   - :origin:`/etc/filtron/rules.json <utils/templates/etc/filtron/rules.json>`

An example configuration can be find below. This configuration limits the access
of:

- scripts or applications (roboagent limit)
- webcrawlers (botlimit)
- IPs which send too many requests (IP limit)
- too many json, csv, etc. requests (rss/json limit)
- the same UserAgent of if too many requests (useragent limit)

.. code:: json

    [
        {
            "name": "search request",
            "filters": [
                "Param:q",
                "Path=^(/|/search)$"
            ],
            "interval": "<time-interval-in-sec (int)>",
            "limit": "<max-request-number-in-interval (int)>",
            "subrules": [
                {
                    "name": "missing Accept-Language",
                    "filters": ["!Header:Accept-Language"],
                    "limit": "<max-request-number-in-interval (int)>",
                    "stop": true,
                    "actions": [
                        {"name":"log"},
                        {"name": "block",
                         "params": {"message": "Rate limit exceeded"}}
                    ]
                },
                {
                    "name": "suspiciously Connection=close header",
                    "filters": ["Header:Connection=close"],
                    "limit": "<max-request-number-in-interval (int)>",
                    "stop": true,
                    "actions": [
                        {"name":"log"},
                        {"name": "block",
                         "params": {"message": "Rate limit exceeded"}}
                    ]
                },
                {
                    "name": "IP limit",
                    "interval": "<time-interval-in-sec (int)>",
                    "limit": "<max-request-number-in-interval (int)>",
                    "stop": true,
                    "aggregations": [
                        "Header:X-Forwarded-For"
                    ],
                    "actions": [
                        { "name": "log"},
                        { "name": "block",
                          "params": {
                              "message": "Rate limit exceeded"
                          }
                        }
                    ]
                },
                {
                    "name": "rss/json limit",
                    "filters": [
                        "Param:format=(csv|json|rss)"
                    ],
                    "interval": "<time-interval-in-sec (int)>",
                    "limit": "<max-request-number-in-interval (int)>",
                    "stop": true,
                    "actions": [
                        { "name": "log"},
                        { "name": "block",
                          "params": {
                              "message": "Rate limit exceeded"
                          }
                        }
                    ]
                },
                {
                    "name": "useragent limit",
                    "interval": "<time-interval-in-sec (int)>",
                    "limit": "<max-request-number-in-interval (int)>",
                    "aggregations": [
                        "Header:User-Agent"
                    ],
                    "actions": [
                        { "name": "log"},
                        { "name": "block",
                          "params": {
                              "message": "Rate limit exceeded"
                          }
                        }
                    ]
                }
            ]
        }
    ]


.. _filtron route request:

Route request through filtron
=============================

.. sidebar:: further reading

   - :ref:`filtron.sh overview`
   - :ref:`installation nginx`
   - :ref:`installation apache`

Filtron can be started using the following command:

.. code:: sh

   $ filtron -rules rules.json

It listens on ``127.0.0.1:4004`` and forwards filtered requests to
``127.0.0.1:8888`` by default.

Use it along with ``nginx`` with the following example configuration.

.. code:: nginx

   # https://example.org/searx

   location /searx {
       proxy_pass         http://127.0.0.1:4004/;

       proxy_set_header   Host             $host;
       proxy_set_header   Connection       $http_connection;
       proxy_set_header   X-Real-IP        $remote_addr;
       proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
       proxy_set_header   X-Scheme         $scheme;
       proxy_set_header   X-Script-Name    /searx;
   }

   location /searx/static {
       /usr/local/searx/searx-src/searx/static;
   }


Requests are coming from port 4004 going through filtron and then forwarded to
port 8888 where a SearXNG is being run. For a complete setup see: :ref:`nginx
searxng site`.
