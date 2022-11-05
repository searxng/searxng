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


OLD_REDIS_URL_DEFAULT_URL = 'unix:///usr/local/searxng-redis/run/redis.sock?db=0'
"""This was the default Redis URL in settings.yml."""

_CLIENT = None
logger = logging.getLogger('searx.shared.redisdb')


def client() -> redis.Redis:
    return _CLIENT


def initialize():
    global _CLIENT  # pylint: disable=global-statement
    redis_url = get_setting('redis.url')
    try:
        if redis_url:
            _CLIENT = redis.Redis.from_url(redis_url)
            logger.info("connected redis: %s", redis_url)
            return True
    except redis.exceptions.ConnectionError:
        _pw = pwd.getpwuid(os.getuid())
        logger.exception("[%s (%s)] can't connect redis DB ...", _pw.pw_name, _pw.pw_uid)
        if redis_url == OLD_REDIS_URL_DEFAULT_URL:
            logger.info(
                "You can safely ignore the above Redis error if you don't use Redis."
                "You can remove this error by setting redis.url to false in your settings.yml."
            )
    return False
