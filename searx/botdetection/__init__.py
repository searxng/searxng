# SPDX-License-Identifier: AGPL-3.0-or-later
""".. _botdetection src:

Implementations used for bot detection.

"""

from ._helpers import dump_request
from ._helpers import get_real_ip
from ._helpers import get_network
from ._helpers import too_many_requests

__all__ = ['dump_request', 'get_network', 'get_real_ip', 'too_many_requests']

redis_client = None
cfg = None


def init(_cfg, _redis_client):
    global redis_client, cfg  # pylint: disable=global-statement
    redis_client = _redis_client
    cfg = _cfg
