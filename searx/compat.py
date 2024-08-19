# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compatibility with older versions"""

# pylint: disable=unused-import

__all__ = [
    "tomllib",
]

import sys

# TOML (lib) compatibility
# ------------------------

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
