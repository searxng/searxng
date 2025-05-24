# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring
from __future__ import annotations

import pathlib

from searx import logger
from searx.cache import ExpireCacheCfg, ExpireCacheSQLite

log = logger.getChild("data")

data_dir = pathlib.Path(__file__).parent

_DATA_CACHE: ExpireCacheSQLite = None  # type: ignore


def get_cache():

    global _DATA_CACHE  # pylint: disable=global-statement

    if _DATA_CACHE is None:
        _DATA_CACHE = ExpireCacheSQLite.build_cache(
            ExpireCacheCfg(
                name="DATA_CACHE",
                # MAX_VALUE_LEN=1024 * 200,  # max. 200kB length for a *serialized* value.
                # MAXHOLD_TIME=60 * 60 * 24 * 7 * 4,  # 4 weeks
            )
        )
    return _DATA_CACHE
