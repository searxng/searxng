# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Initialization of a *shared* storage.

The *shared* :py:obj:`storage` is a dictionary type that is stored:

- in a redis DB.  If a redis DB is not available it is stored
- in a uWSGI cache. If no uWSGI is not available it is stored
- in a simple python dictionary.
"""

import logging
from . import redisdb

logger = logging.getLogger('searx.shared')

__all__ = ["storage", "schedule"]

if redisdb.init():
    # First: try to use Redis

    from .shared_redis import RedisCacheSharedDict as SharedDict, schedule

    logger.info('Use shared_redis implementation')

else:
    # Second: try to use uwsgi

    logger.error("can't connect redis DB, try to init uWSGI cache")
    try:
        import uwsgi  # type: ignore

        logger.info('Use shared_uwsgi implementation')
        uwsgi.cache_update('dummy', b'dummy')
        if uwsgi.cache_get('dummy') != b'dummy':
            logger.error('found issues when using uWSGI, fall back to python dictionary')
            from .shared_simple import SimpleSharedDict as SharedDict, schedule

    except ModuleNotFoundError:
        # Third: fall back to shared_simple

        logger.error("uWSGI is not available, fall back to python dictionary")
        from .shared_simple import SimpleSharedDict as SharedDict, schedule

storage = SharedDict()
