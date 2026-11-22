# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import MagicMock

from searx.engines import yacy
from tests import SearxTestCase


class TestYacy(SearxTestCase):

    def test_invalid_json_returns_empty(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html>error page</html>"
        self.assertEqual(yacy.response(resp), [])
