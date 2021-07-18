# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-function-docstring, missing-module-docstring

from os.path import dirname, abspath
import logging

import searx.unixthreadname
import searx.settings_loader
from searx.settings_defaults import settings_set_defaults

searx_dir = abspath(dirname(__file__))
searx_parent_dir = abspath(dirname(dirname(__file__)))
settings, settings_load_message = searx.settings_loader.load_settings()

if settings is not None:
    settings = settings_set_defaults(settings)

searx_debug = settings['general']['debug']
if searx_debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger('searx')
logger.info(settings_load_message)

# log max_request_timeout
max_request_timeout = settings['outgoing']['max_request_timeout']
if max_request_timeout is None:
    logger.info('max_request_timeout=%s', repr(max_request_timeout))
else:
    logger.info('max_request_timeout=%i second(s)', max_request_timeout)

_unset = object()

def get_setting(name, default=_unset):
    """Returns the value to which ``name`` point.  If there is no such name in the
    settings and the ``default`` is unset, a :py:obj:`KeyError` is raised.

    """
    value = settings
    for a in name.split('.'):
        if isinstance(value, dict):
            value = value.get(a, _unset)
        else:
            value = _unset

        if value is _unset:
            if default is _unset:
                raise KeyError(name)
            value = default
            break

    return value
