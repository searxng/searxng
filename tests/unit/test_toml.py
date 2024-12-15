# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from tests import SearxTestCase
from searx import compat
from searx.favicons.config import DEFAULT_CFG_TOML_PATH


class CompatTest(SearxTestCase):

    def test_toml(self):
        with DEFAULT_CFG_TOML_PATH.open("rb") as f:
            _ = compat.tomllib.load(f)
