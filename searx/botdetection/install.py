# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""see :ref:`limiter src`"""

import sys
import flask

from searx import redisdb, logger
from searx.botdetection import limiter

# the configuration are limiter.toml and "limiter" in settings.yml
# so, for coherency, the logger is "limiter" even if the module name "searx.botdetection"
logger = logger.getChild('limiter')


_INSTALLED = False


def pre_request():
    """See :ref:`flask.Flask.before_request`"""
    return limiter.filter_request(flask.request)


def is_installed():
    return _INSTALLED


def initialize(app: flask.Flask, settings):
    """Instal the botlimiter aka limiter"""
    global _INSTALLED  # pylint: disable=global-statement
    if not settings['server']['limiter'] and not settings['server']['public_instance']:
        return
    if not redisdb.client():
        logger.error(
            "The limiter requires Redis, please consult the documentation: "
            + "https://docs.searxng.org/admin/searx.botdetection.html#limiter"
        )
        if settings['server']['public_instance']:
            sys.exit(1)
        return
    app.before_request(pre_request)
    _INSTALLED = True
