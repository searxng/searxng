# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
""".. _botdetection src:

Implementations used for bot detection.

"""
from __future__ import annotations

from dataclasses import dataclass
import pathlib

import redis
from .config import Config

from ._helpers import logger
from ._helpers import dump_request
from ._helpers import get_real_ip
from ._helpers import get_network
from ._helpers import too_many_requests

logger = logger.getChild('init')

__all__ = ['dump_request', 'get_network', 'get_real_ip', 'too_many_requests']

CFG_SCHEMA = pathlib.Path(__file__).parent / "schema.toml"
"""Base configuration (schema) of the botdetection."""

CFG_DEPRECATED = {
    # "dummy.old.foo": "config 'dummy.old.foo' exists only for tests.  Don't use it in your real project config."
}


@dataclass
class Context:
    """A global context of the botdetection"""

    # pylint: disable=too-few-public-methods

    redis_client: redis.Redis | None = None
    cfg: Config = Config.from_toml(schema_file=CFG_SCHEMA, cfg_file=None, deprecated=CFG_DEPRECATED)

    def init(self, toml_cfg: pathlib.Path, redis_client: redis.Redis | None):
        self.redis_client = redis_client
        self.cfg.load_toml(toml_cfg)


ctx = Context()
