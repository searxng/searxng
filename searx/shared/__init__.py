# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

logger = logging.getLogger('searx.shared')

try:
    import uwsgi
except:
    # no uwsgi
    from .shared_simple import SimpleSharedDict as SharedDict, schedule

    logger.info('Use shared_simple implementation')
else:
    try:
        uwsgi.cache_update('dummy', b'dummy')
        if uwsgi.cache_get('dummy') != b'dummy':
            raise Exception()
    except:
        # uwsgi.ini configuration problem: disable all scheduling
        logger.error(
            'uwsgi.ini configuration error, add this line to your uwsgi.ini\n'
            'cache2 = name=searxcache,items=2000,blocks=2000,blocksize=4096,bitmap=1'
        )
        from .shared_simple import SimpleSharedDict as SharedDict

        def schedule(delay, func, *args):
            return False

    else:
        # uwsgi
        from .shared_uwsgi import UwsgiCacheSharedDict as SharedDict, schedule

        logger.info('Use shared_uwsgi implementation')

storage = SharedDict()
