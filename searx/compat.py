# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compatibility with older versions"""

# pylint: disable=unused-import

__all__ = [
    "tomllib",
]

import os
import sys
import typing as t
import warnings


# TOML (lib) compatibility
# ------------------------

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# limiter backward compatibility
# ------------------------------

LIMITER_CFG_DEPRECATED = {
    "real_ip": "limiter: config section 'real_ip' is deprecated",
    "real_ip.x_for": "real_ip.x_for has been replaced by botdetection.trusted_proxies",
    "real_ip.ipv4_prefix": "real_ip.ipv4_prefix has been replaced by botdetection.ipv4_prefix",
    "real_ip.ipv6_prefix": "real_ip.ipv6_prefix has been replaced by botdetection.ipv6_prefix'",
}

ABUSEIPDB_ENV_VARS = {
    "botdetection.abuseipdb.enabled": "SEARXNG_ABUSEIPDB_ENABLED",
    "botdetection.abuseipdb.api_key": "SEARXNG_ABUSEIPDB_API_KEY",
    "botdetection.abuseipdb.confidence_threshold": "SEARXNG_ABUSEIPDB_CONFIDENCE_THRESHOLD",
    "botdetection.abuseipdb.skip_tor": "SEARXNG_ABUSEIPDB_SKIP_TOR",
    "botdetection.abuseipdb.cache_time": "SEARXNG_ABUSEIPDB_CACHE_TIME",
}


def _convert_env_value(key: str, value: str) -> t.Any:
    """Convert environment variable value to appropriate type."""
    if key.endswith(".enabled") or key.endswith(".skip_tor"):
        return value.lower() in ("1", "true", "yes", "on")
    if key.endswith(".confidence_threshold") or key.endswith(".cache_time"):
        try:
            return int(value)
        except ValueError:
            return value
    return value


def limiter_fix_cfg(cfg, cfg_file):

    kwargs = {
        "category": DeprecationWarning,
        "filename": str(cfg_file),
        "lineno": 0,
        "module": "searx.limiter",
    }

    for opt, msg in LIMITER_CFG_DEPRECATED.items():
        try:
            val = cfg.get(opt)
        except KeyError:
            continue

        warnings.warn_explicit(msg, **kwargs)
        if opt == "real_ip.ipv4_prefix":
            cfg.set("botdetection.ipv4_prefix", val)
        if opt == "real_ip.ipv6_prefix":
            cfg.set("botdetection.ipv6_prefix", val)

    for opt, env_var in ABUSEIPDB_ENV_VARS.items():
        if env_var in os.environ:
            value = _convert_env_value(opt, os.environ[env_var])
            try:
                cfg.set(opt, value)
            except KeyError:
                pass
