# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Implement some checks in the active installation
"""

import os
import sys
import logging
import warnings

LOG_FORMAT_DEBUG = '%(levelname)-7s %(name)-30.30s: %(message)s'
logging.basicConfig(level=logging.getLevelName('DEBUG'), format=LOG_FORMAT_DEBUG)
os.environ['SEARXNG_DEBUG'] = '1'

# from here on implement the checks of the installation

import searx

OLD_SETTING = '/etc/searx/settings.yml'

if os.path.isfile(OLD_SETTING):
    msg = (
        '%s is no longer valid, move setting to %s' % (
            OLD_SETTING,
            os.environ.get('SEARXNG_SETTINGS_PATH', '/etc/searxng/settings.yml')
        ))
    warnings.warn(msg, DeprecationWarning)

from searx import redisdb, get_setting

if not redisdb.initialize():
    warnings.warn("can't connect to redis DB at: %s" % get_setting('redis.url'), RuntimeWarning, stacklevel=2)
    warnings.warn("--> no bot protection without redis DB", RuntimeWarning, stacklevel=2)
