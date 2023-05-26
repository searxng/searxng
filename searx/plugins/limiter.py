# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""see :ref:`limiter src`"""

import flask

from searx import redisdb
from searx.plugins import logger
from searx.botdetection import limiter
from searx.botdetection import dump_request

name = "Request limiter"
description = "Limit the number of request"
default_on = False
preference_section = 'service'

logger = logger.getChild('limiter')


def pre_request():
    """See :ref:`flask.Flask.before_request`"""

    val = limiter.filter_request(flask.request)
    if val is not None:
        http_status, msg = val
        client_ip = flask.request.headers.get('X-Forwarded-For', '<unknown>')
        logger.error("BLOCK (IP %s): %s" % (client_ip, msg))
        return 'Too Many Requests', http_status

    logger.debug("OK: %s" % dump_request(flask.request))
    return None


def init(app: flask.Flask, settings) -> bool:
    if not settings['server']['limiter']:
        return False
    if not redisdb.client():
        logger.error("The limiter requires Redis")
        return False
    limiter.init_cfg(logger)
    app.before_request(pre_request)
    return True
