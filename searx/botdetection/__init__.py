# SPDX-License-Identifier: AGPL-3.0-or-later
""".. _botdetection src:

Implementations used for bot detection.

"""
from __future__ import annotations

import valkey

from ._helpers import dump_request
from ._helpers import get_real_ip
from ._helpers import get_network
from ._helpers import too_many_requests
from . import config
from . import valkeydb

__all__ = ['init', 'dump_request', 'get_network', 'get_real_ip', 'too_many_requests']


def init(cfg, valkey_client: valkey.Valkey | None):
    config.set_global_cfg(cfg)
    if valkey_client:
        valkeydb.set_valkey_client(valkey_client)
