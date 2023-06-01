# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
""".. _botdetection src:

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
