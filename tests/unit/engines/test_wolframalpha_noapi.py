# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

from unittest.mock import MagicMock, patch

from searx.engines import wolframalpha_noapi
from tests import SearxTestCase


class TestWolframAlphaNoApi(SearxTestCase):

    def test_obtain_token_caches_under_token(self):
        cache = MagicMock()
        cache.get.return_value = None
        resp = MagicMock()
        resp.json.return_value = {"code": "TOK"}

        with (
            patch.object(wolframalpha_noapi, "CACHE", cache, create=True),
            patch.object(wolframalpha_noapi, "http_get", return_value=resp),
        ):
            self.assertEqual(wolframalpha_noapi.obtain_token(), "TOK")

        cache.set.assert_called_once_with(key="token", value="TOK", expire=3600)
