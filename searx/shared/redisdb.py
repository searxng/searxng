# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Implementation of the redis client (redis-py_).

.. _redis-py: https://github.com/redis/redis-py

This implementation uses the :ref:`settings redis` setup from ``settings.yml``.
A redis DB connect can be tested by::

  >>> from searx.shared import redisdb
  >>> redisdb.init()
  True
  >>> db = redisdb.client()
  >>> db.set("foo", "bar")
  True
  >>> db.get("foo")
  b'bar'
  >>>

"""

import logging
import redis
from searx import get_setting

logger = logging.getLogger('searx.shared.redis')
_client = None


def client():
    global _client  # pylint: disable=global-statement
    if _client is None:
        # not thread safe: in the worst case scenario, two or more clients are
        # initialized only one is kept, the others are garbage collected.
        _client = redis.Redis.from_url(get_setting('redis.url'))
    return _client


def init():
    try:
        c = client()
        logger.info("connected redis DB --> %s", c.acl_whoami())
        return True
    except redis.exceptions.ConnectionError as exc:
        logger.error("can't connet redis DB ...")
        logger.error("  %s", exc)
    return False
