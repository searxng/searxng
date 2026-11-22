# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name

import typing as t
from unittest.mock import MagicMock, patch

from searx.engines import duckduckgo_extra
from searx.search.processors import OnlineParams
from tests import SearxTestCase


class TestDuckDuckGoExtra(SearxTestCase):

    def test_fetch_vqd_uses_engine_category(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = 'vqd="abc123"'
        params = t.cast("OnlineParams", t.cast(object, {"headers": {}, "impersonate": "chrome"}))

        with (
            patch.object(duckduckgo_extra, "ddg_category", "news"),
            patch.object(duckduckgo_extra, "get", return_value=resp) as get_mock,
            patch.object(duckduckgo_extra, "set_vqd"),
        ):
            duckduckgo_extra.fetch_vqd("test", params)

        url = get_mock.call_args.kwargs["url"]
        self.assertIn("iar=news", url)
