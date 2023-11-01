# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring

import sys
import os
from os.path import dirname, abspath

import logging

import searx.unixthreadname
import searx.settings_loader
from searx.settings_defaults import settings_set_defaults


# Debug
LOG_FORMAT_DEBUG = '%(levelname)-7s %(name)-30.30s: %(message)s'

# Production
LOG_FORMAT_PROD = '%(asctime)-15s %(levelname)s:%(name)s: %(message)s'
LOG_LEVEL_PROD = logging.WARNING

searx_dir = abspath(dirname(__file__))
searx_parent_dir = abspath(dirname(dirname(__file__)))
settings, settings_load_message = searx.settings_loader.load_settings()

if settings is not None:
    settings = settings_set_defaults(settings)

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


def is_color_terminal():
    if os.getenv('TERM') in ('dumb', 'unknown'):
        return False
    return sys.stdout.isatty()


def logging_config_debug():
    try:
        import coloredlogs  # pylint: disable=import-outside-toplevel
    except ImportError:
        coloredlogs = None

    log_level = os.environ.get('SEARXNG_DEBUG_LOG_LEVEL', 'DEBUG')
    if coloredlogs and is_color_terminal():
        level_styles = {
            'spam': {'color': 'green', 'faint': True},
            'debug': {},
            'notice': {'color': 'magenta'},
            'success': {'bold': True, 'color': 'green'},
            'info': {'bold': True, 'color': 'cyan'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'bold': True, 'color': 'red'},
        }
        field_styles = {
            'asctime': {'color': 'green'},
            'hostname': {'color': 'magenta'},
            'levelname': {'color': 8},
            'name': {'color': 8},
            'programname': {'color': 'cyan'},
            'username': {'color': 'yellow'},
        }
        coloredlogs.install(level=log_level, level_styles=level_styles, field_styles=field_styles, fmt=LOG_FORMAT_DEBUG)
    else:
        logging.basicConfig(level=logging.getLevelName(log_level), format=LOG_FORMAT_DEBUG)


searx_debug = settings['general']['debug']
if searx_debug:
    logging_config_debug()
else:
    logging.basicConfig(level=LOG_LEVEL_PROD, format=LOG_FORMAT_PROD)
    logging.root.setLevel(level=LOG_LEVEL_PROD)
    logging.getLogger('werkzeug').setLevel(level=LOG_LEVEL_PROD)
logger = logging.getLogger('searx')
logger.info(settings_load_message)

# log max_request_timeout
max_request_timeout = settings['outgoing']['max_request_timeout']
if max_request_timeout is None:
    logger.info('max_request_timeout=%s', repr(max_request_timeout))
else:
    logger.info('max_request_timeout=%i second(s)', max_request_timeout)
