# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compatibility with older versions"""

# pylint: disable=unused-import

__all__ = [
    "tomllib",
]

import sys
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
