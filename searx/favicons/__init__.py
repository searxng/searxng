# SPDX-License-Identifier: AGPL-3.0-or-later
"""Implementations for providing the favicons in SearXNG.

There is a command line for developer purposes and for deeper analysis.  Here is
an example in which the command line is called in the development environment::

  $ ./manage pyenv.cmd bash --norc --noprofile
  (py3) python -m searx.favicons --help
"""

from __future__ import annotations

__all__ = ["init", "favicon_url", "favicon_proxy"]

import pathlib
from searx import logger
from searx import get_setting
from .proxy import favicon_url, favicon_proxy

logger = logger.getChild('favicons')


def is_active():
    return bool(get_setting("search.favicon_resolver", False))


def init():

    # pylint: disable=import-outside-toplevel

    from . import config, cache, proxy
    from .. import settings_loader

    cfg_file = (settings_loader.get_user_cfg_folder() or pathlib.Path("/etc/searxng")) / "favicons.toml"
    if not cfg_file.exists():
        if is_active():
            logger.error(f"missing favicon config: {cfg_file}")
        cfg_file = config.DEFAULT_CFG_TOML_PATH

    logger.debug(f"load favicon config: {cfg_file}")
    cfg = config.FaviconConfig.from_toml_file(cfg_file, use_cache=True)
    cache.init(cfg.cache)
    proxy.init(cfg.proxy)

    del cache, config, proxy, cfg, settings_loader
