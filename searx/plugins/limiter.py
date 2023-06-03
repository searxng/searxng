# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""see :ref:`limiter src`"""

import flask

from searx import redisdb
from searx.plugins import logger
from searx.botdetection import limiter

name = "Request limiter"
description = "Limit the number of request"
default_on = False
preference_section = 'service'

logger = logger.getChild('limiter')


def pre_request():
    """See :ref:`flask.Flask.before_request`"""
    return limiter.filter_request(flask.request)


def init(app: flask.Flask, settings) -> bool:
    if not settings['server']['limiter']:
        return False
    if not redisdb.client():
        logger.error("The limiter requires Redis")
        return False
    app.before_request(pre_request)
    return True
