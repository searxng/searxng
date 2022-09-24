# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Module implements a :py:obj:`storage`."""

__all__ = ['schedule', 'storage']

import logging
import importlib

from . import redisdb
from . import shared_redis
from . import shared_simple

logger = logging.getLogger('searx.shared')

SharedDict = None
schedule = None

if redisdb.init():
    SharedDict = shared_redis.RedisCacheSharedDict
    logger.info('use redis DB for SharedDict')

try:
    from . import shared_uwsgi
    uwsgi = importlib.import_module('uwsgi')
    uwsgi.cache_update('dummy', b'dummy')
    if uwsgi.cache_get('dummy') != b'dummy':
        raise Exception()

    schedule = shared_uwsgi.schedule
    logger.info('use shared_uwsgi for schedule')

    if SharedDict is None:
        SharedDict = shared_simple.SimpleSharedDict
        logger.info('use shared_uwsgi for SharedDict')

except Exception:  # pylint: disable=broad-except
    logger.debug('skip uwsgi setup ..', exc_info=1)

if SharedDict is None:
    logger.info('use shared_simple for SharedDict')
    SharedDict = shared_simple.SimpleSharedDict

if schedule is None:
    logger.info('use shared_simple for schedule')
    schedule = shared_simple.schedule

storage = SharedDict(key_prefix='SearXNG_storage')
