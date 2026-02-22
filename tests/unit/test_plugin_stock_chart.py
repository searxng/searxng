# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from parameterized.parameterized import parameterized

import searx.plugins
import searx.preferences
from searx.extended_types import sxng_request
from searx.plugins.stock_chart import StockChartAnswer
from tests import SearxTestCase

from .test_plugins import do_post_search


def _fake_polygon_results(prices: list[float]) -> dict[str, Any]:
    # Build minimal Polygon-like payload with ascending timestamps
    base_ts = 1_735_000_000_000
    results = []
    for idx, c in enumerate(prices):
        results.append(
            {
                "v": 1_000_000 + idx,
                "vw": c,
                "o": c,
                "c": c,
                "h": c,
                "l": c,
                "t": base_ts + idx * 86_400_000,
                "n": 1_000 + idx,
            }
        )
    return {"status": "OK", "results": results}


class PluginStockChartTest(SearxTestCase):
    def setUp(self) -> None:
        super().setUp()
        engines: dict[str, Any] = {}

        self.storage = searx.plugins.PluginStorage()
        self.storage.load_settings({"searx.plugins.stock_chart.SXNGPlugin": {"active": True}})
        self.storage.init(self.app)
        self.pref = searx.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def _with_prefs(self, *, token: str | None, timeframe: int | None) -> None:
        data: dict[str, str] = {"locale": "en"}
        if token is not None:
            data["stock_chart_token"] = token
        if timeframe is not None:
            data["stock_chart_timeframe"] = str(timeframe)
        self.pref.parse_dict(data)

    def _do_search(self, query: str, *, pageno: int = 1):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            return do_post_search(query, self.storage, pageno=pageno)

    def test_plugin_store_init(self) -> None:
        assert len(self.storage) == 1

    @parameterized.expand(
        [
            ("nvda", "NVDA"),
            ("nvda stock", "NVDA"),
            ("30292NAG7", "30292NAG7"),  # CUSIP
            ("US0378331005", "US0378331005"),  # ISIN (AAPL)
            ("ms.ft", "MS.FT"),  # dot allowed
        ]
    )
    def test_normalize_accepts_identifiers(self, query: str, expected: str) -> None:
        self._with_prefs(token="TKN", timeframe=10)
        with patch(
            "searx.plugins.stock_chart._fetch_polygon_data",
            return_value=_fake_polygon_results([1.0, 2.0]),
        ) as mocked:
            search = self._do_search(query)
        # Answer exists and symbol uppercased as expected
        assert search.result_container.answers
        ans = next(iter(search.result_container.answers))
        assert isinstance(ans, StockChartAnswer)
        assert ans.symbol == expected
        # Helper called with normalized symbol
        mocked.assert_called()
        called_symbol = mocked.call_args[0][0]
        assert called_symbol == expected

    @parameterized.expand(
        [
            (None, 30),  # IntegerSetting default is 30, not None
            (5, 5),
            (21, 21),
        ]
    )
    def test_timeframe_preference_and_default(self, user_timeframe: int | None, expected_days: int) -> None:
        self._with_prefs(token="TKN", timeframe=user_timeframe)
        with patch(
            "searx.plugins.stock_chart._fetch_polygon_data",
            return_value=_fake_polygon_results([10.0, 11.0]),
        ) as mocked:
            self._do_search("nvda")
            # Ensure helper is called with expected timeframe days
            assert mocked.called
            assert mocked.call_args[0][2] == expected_days

    def test_no_token_means_no_answer(self) -> None:
        self._with_prefs(token=None, timeframe=10)
        with patch("searx.plugins.stock_chart._fetch_polygon_data") as mocked:
            search = self._do_search("nvda")
            assert not search.result_container.answers
            mocked.assert_not_called()

    def test_pageno_greater_than_one_noops(self) -> None:
        self._with_prefs(token="TKN", timeframe=10)
        with patch("searx.plugins.stock_chart._fetch_polygon_data") as mocked:
            search = self._do_search("nvda", pageno=2)
            assert not search.result_container.answers
            mocked.assert_not_called()

    @parameterized.expand(
        [
            ("hello world",),
            ("not-a-security query",),
        ]
    )
    def test_non_identifier_queries_are_ignored(self, query: str) -> None:
        self._with_prefs(token="TKN", timeframe=10)
        with patch("searx.plugins.stock_chart._fetch_polygon_data") as mocked:
            search = self._do_search(query)
            assert not search.result_container.answers
            mocked.assert_not_called()

    @parameterized.expand(
        [
            ({"status": "OK", "results": []},),
            (None,),
        ]
    )
    def test_api_returns_no_results(self, payload: dict[str, Any] | None) -> None:
        self._with_prefs(token="TKN", timeframe=10)
        with patch(
            "searx.plugins.stock_chart._fetch_polygon_data",
            return_value=payload,
        ):
            search = self._do_search("nvda")
            assert not search.result_container.answers

    def test_answer_fields_are_populated(self) -> None:
        self._with_prefs(token="TKN", timeframe=10)
        prices = [100.0, 101.5, 102.0]
        payload = _fake_polygon_results(prices)
        with patch(
            "searx.plugins.stock_chart._fetch_polygon_data",
            return_value=payload,
        ):
            search = self._do_search("AAPL")
        assert search.result_container.answers
        ans = next(iter(search.result_container.answers))
        assert isinstance(ans, StockChartAnswer)
        assert ans.symbol == "AAPL"
        assert ans.last_price == prices[-1]
        assert ans.previous_close == prices[-2]
        assert ans.closes == prices
        assert len(ans.times) == len(prices)
        assert ans.currency == "USD"
        assert ans.market_data == payload["results"]
