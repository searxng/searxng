# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from __future__ import annotations

import pathlib
import msgspec

from .cache import FaviconCacheConfig
from .proxy import FaviconProxyConfig

CONFIG_SCHEMA: int = 1
"""Version of the configuration schema."""

TOML_CACHE_CFG: dict[str, "FaviconConfig"] = {}
"""Cache config objects by TOML's filename."""

DEFAULT_CFG_TOML_PATH = pathlib.Path(__file__).parent / "favicons.toml"


class FaviconConfig(msgspec.Struct):  # pylint: disable=too-few-public-methods
    """The class aggregates configurations of the favicon tools"""

    cfg_schema: int
    """Config's schema version.  The specification of the version of the schema
    is mandatory, currently only version :py:obj:`CONFIG_SCHEMA` is supported.
    By specifying a version, it is possible to ensure downward compatibility in
    the event of future changes to the configuration schema"""

    cache: FaviconCacheConfig = msgspec.field(default_factory=FaviconCacheConfig)
    """Setup of the :py:obj:`.cache.FaviconCacheConfig`."""

    proxy: FaviconProxyConfig = msgspec.field(default_factory=FaviconProxyConfig)
    """Setup of the :py:obj:`.proxy.FaviconProxyConfig`."""

    @classmethod
    def from_toml_file(cls, cfg_file: pathlib.Path, use_cache: bool) -> "FaviconConfig":
        """Create a config object from a TOML file, the ``use_cache`` argument
        specifies whether a cache should be used.
        """

        cached = TOML_CACHE_CFG.get(str(cfg_file))
        if use_cache and cached:
            return cached

        with cfg_file.open("rb") as f:
            data = f.read()

        cfg = msgspec.toml.decode(data, type=_FaviconConfig)
        schema = cfg.favicons.cfg_schema
        if schema != CONFIG_SCHEMA:
            raise ValueError(
                f"config schema version {CONFIG_SCHEMA} is needed, version {schema} is given in {cfg_file}"
            )

        cfg = cfg.favicons
        if use_cache and cached:
            TOML_CACHE_CFG[str(cfg_file.resolve())] = cfg

        return cfg


class _FaviconConfig(msgspec.Struct):  # pylint: disable=too-few-public-methods
    # wrapper struct for root object "favicons."
    favicons: FaviconConfig
