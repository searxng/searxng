# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, cyclic-import
from __future__ import annotations

import typing as t
import sys
import os
from os.path import dirname, abspath

import logging

import msgspec

# Debug
LOG_FORMAT_DEBUG: str = '%(levelname)-7s %(name)-30.30s: %(message)s'

# Production
LOG_FORMAT_PROD: str = '%(asctime)-15s %(levelname)s:%(name)s: %(message)s'
LOG_LEVEL_PROD = logging.WARNING

searx_dir: str = abspath(dirname(__file__))
searx_parent_dir: str = abspath(dirname(dirname(__file__)))

settings: dict[str, t.Any] = {}

sxng_debug: bool = False
logger = logging.getLogger('searx')

_unset = object()


def init_settings():
    """Initialize global ``settings`` and ``sxng_debug`` variables and
    ``logger`` from ``SEARXNG_SETTINGS_PATH``.
    """

    # pylint: disable=import-outside-toplevel
    from searx import settings_loader
    from searx.settings_defaults import SCHEMA, apply_schema

    global settings, sxng_debug  # pylint: disable=global-variable-not-assigned

    cfg, msg = settings_loader.load_settings(load_user_settings=True)
    cfg = cfg or {}
    apply_schema(cfg, SCHEMA, [])

    settings.clear()
    settings.update(cfg)

    sxng_debug = get_setting("general.debug")
    if sxng_debug:
        _logging_config_debug()
    else:
        logging.basicConfig(level=LOG_LEVEL_PROD, format=LOG_FORMAT_PROD)
        logging.root.setLevel(level=LOG_LEVEL_PROD)
        logging.getLogger('werkzeug').setLevel(level=LOG_LEVEL_PROD)
        logger.info(msg)

    # log max_request_timeout
    max_request_timeout: int | None = settings['outgoing']['max_request_timeout']
    if max_request_timeout is None:
        logger.info('max_request_timeout=%s', repr(max_request_timeout))
    else:
        logger.info('max_request_timeout=%i second(s)', max_request_timeout)

    if settings['server']['public_instance']:
        logger.warning(
            "Be aware you have activated features intended only for public instances. "
            "This force the usage of the limiter and link_token / "
            "see https://docs.searxng.org/admin/searx.limiter.html"
        )


def get_setting(name: str, default: t.Any = _unset) -> t.Any:
    """Returns the value to which ``name`` point.  If there is no such name in the
    settings and the ``default`` is unset, a :py:obj:`KeyError` is raised.

    """
    value = settings
    for a in name.split('.'):
        if isinstance(value, msgspec.Struct):
            value = getattr(value, a, _unset)
        elif isinstance(value, dict):
            value = value.get(a, _unset)  # pyright: ignore
        else:
            value = _unset

        if value is _unset:
            if default is _unset:
                raise KeyError(name)
            value = default
            break

    return value  # pyright: ignore


def _is_color_terminal():
    if os.getenv('TERM') in ('dumb', 'unknown'):
        return False
    return sys.stdout.isatty()


def _logging_config_debug():
    try:
        import coloredlogs  # pylint: disable=import-outside-toplevel
    except ImportError:
        coloredlogs = None

    log_level = os.environ.get('SEARXNG_DEBUG_LOG_LEVEL', 'DEBUG')
    if coloredlogs and _is_color_terminal():
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
        coloredlogs.install(  # type: ignore
            level=log_level,
            level_styles=level_styles,
            field_styles=field_styles,
            fmt=LOG_FORMAT_DEBUG,
        )
    else:
        logging.basicConfig(level=getattr(logging, log_level, "ERROR"), format=LOG_FORMAT_DEBUG)


init_settings()
