# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

logger = logging.getLogger('searx.shared')

__all__ = ["storage", "schedule"]


try:
    # First: try to use Redis
    from .redisdb import client

    client().ping()
    from .shared_redis import RedisCacheSharedDict as SharedDict, schedule

    logger.info('Use shared_redis implementation')
except Exception as e:
    # Second: try to use uwsgi
    try:
        import uwsgi
    except:
        # Third : fall back to shared_simple
        from .shared_simple import SimpleSharedDict as SharedDict, schedule

        logger.info('Use shared_simple implementation')
    else:
        # Make sure uwsgi is okay
        try:
            uwsgi.cache_update('dummy', b'dummy')
            if uwsgi.cache_get('dummy') != b'dummy':
                raise Exception()  # pylint: disable=raise-missing-from
        except:
            # there is exception on a get/set test: disable all scheduling
            logger.exception(
                'uwsgi.ini configuration error, add this line to your uwsgi.ini\n'
                'cache2 = name=searxngcache,items=2000,blocks=2000,blocksize=4096,bitmap=1\n'
            )
            from .shared_simple import SimpleSharedDict as SharedDict

            def schedule(delay, func, *args):
                return False

        else:
            # use uwsgi
            from .shared_uwsgi import UwsgiCacheSharedDict as SharedDict, schedule

            logger.info('Use shared_uwsgi implementation')

storage = SharedDict()
