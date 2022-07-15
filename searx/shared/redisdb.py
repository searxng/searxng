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

import os
import pwd
import logging
import redis
from searx import get_setting


logger = logging.getLogger('searx.shared.redisdb')
_client = None


def client() -> redis.Redis:
    return _client


def initialize():
    global _client  # pylint: disable=global-statement
    try:
        _client = redis.Redis.from_url(get_setting('redis.url'))
        logger.info("connected redis: %s", get_setting('redis.url'))
    except redis.exceptions.ConnectionError as exc:
        _pw = pwd.getpwuid(os.getuid())
        logger.error("[%s (%s)] can't connect redis DB ...", _pw.pw_name, _pw.pw_uid)
        logger.error("  %s", exc)
