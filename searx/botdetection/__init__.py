# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
""".. _botdetection src:

The :ref:`limiter <limiter src>` implements several methods to block bots:

a. Analysis of the HTTP header in the request / can be easily bypassed.

b. Block and pass lists in which IPs are listed / difficult to maintain, since
   the IPs of bots are not all known and change over the time.

c. Detection of bots based on the behavior of the requests and blocking and, if
   necessary, unblocking of the IPs via a dynamically changeable IP block list.

For dynamically changeable IP lists a Redis database is needed and for any kind
of IP list the determination of the IP of the client is essential.  The IP of
the client is determined via the X-Forwarded-For_ HTTP header

.. _X-Forwarded-For:
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Forwarded-For

X-Forwarded-For
===============

.. attention::

   A correct setup of the HTTP request headers ``X-Forwarded-For`` and
   ``X-Real-IP`` is essential to be able to assign a request to an IP correctly:

   - `NGINX RequestHeader`_
   - `Apache RequestHeader`_

.. _NGINX RequestHeader:
    https://docs.searxng.org/admin/installation-nginx.html#nginx-s-searxng-site
.. _Apache RequestHeader:
    https://docs.searxng.org/admin/installation-apache.html#apache-s-searxng-site

.. autofunction:: searx.botdetection.get_real_ip

"""

from ._helpers import dump_request
from ._helpers import get_real_ip
from ._helpers import too_many_requests
