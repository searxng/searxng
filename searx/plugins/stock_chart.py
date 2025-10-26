# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stock chart answer plugin using Polygon.io API.

This plugin detects short security identifiers (tickers, ISIN, CUSIP, etc.)
in the user's query and, when possible, shows a small historical price chart
as an answer. It fails fast and returns no results for non-security queries.

Configuration (settings.yml):

    plugins:
      searx.plugins.stock_chart.SXNGPlugin:
        active: true
        token: "YOUR_POLYGON_TOKEN"
        timeframe_days: 7   # optional, default 7

"""

from __future__ import annotations

import re
import typing as t
from dataclasses import field
from datetime import datetime, timedelta, timezone

from flask_babel import gettext
from httpx import HTTPError

from searx.network import get
from searx.result_types import EngineResults
from searx.result_types.answer import BaseAnswer

from . import Plugin, PluginInfo

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Request
    from searx.search import SearchWithPlugins

    from . import PluginCfg


# -------------------------------
# Helpers and data structures
# -------------------------------


class StockChartAnswer(BaseAnswer, kw_only=True):
    """Answer type for a small inline stock sparkline chart.

    Attributes
    ----------
    symbol : str
        Resolved trading symbol (e.g. ``NVDA``).
    name : str
        Company/security name when available.
    last_price : float
        Latest close/price in the fetched window.
    previous_close : float | None
        Previous close before the last price (if available) used for delta.
    closes : list[float]
        Close prices in chronological order used to render the chart path.
    times : list[int]
        UNIX timestamps aligned with ``closes``.
    currency : str
        Currency code when available from lookup.
    url : str | None
        Optional URL to an external quote page.
    timeframe_days : int
        Number of days of data shown in the chart.
    market_data : list[dict]
        Raw market data from API with volume, high, low, open, etc.
    """

    template: str = "answer/stock_chart.html"

    symbol: str
    name: str
    last_price: float
    previous_close: float | None
    closes: list[float]
    times: list[int]
    currency: str = ""
    url: str | None = None
    timeframe_days: int = 7
    market_data: list[dict] = field(default_factory=list)  # pylint: disable=invalid-field-call

    def __hash__(self) -> int:
        """Two charts for the same symbol are considered identical."""
        return hash(f"stock_chart:{self.symbol}")


def _normalize_identifier(raw_query: str) -> str | None:
    """Detect and extract a likely security identifier from ``raw_query``.

    Accepted forms include:
    - Bare identifier: ``nvda``, ``ko``, ``msft``
    - With trailing "stock": ``nvda stock``
    - Common identifiers: tickers (1-7 alnum incl. .-), CUSIP (9 chars),
      ISIN (2 letters + 10 alnum)

    Returns the cleaned identifier in uppercase, or ``None`` if it doesn't
    look like a security identifier.
    """
    q = raw_query.strip().upper()
    parts = q.split()
    if len(parts) == 2 and parts[1] in {"STOCK", "STOCKS"}:
        q = parts[0]
    elif len(parts) != 1:
        return None

    # ISIN: 2 letters + 10 alnum (total 12)
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", q):
        return q

    # CUSIP: 9 alnum
    if re.fullmatch(r"[A-Z0-9]{9}", q):
        return q

    # Ticker-like: 1-7 of [A-Z0-9.-], must start with a letter
    if re.fullmatch(r"[A-Z][A-Z0-9.-]{0,6}", q):
        return q

    return None


def _fetch_polygon_data(symbol: str, token: str, days: int) -> dict[str, t.Any] | None:
    """Fetch stock data from Polygon.io API.

    Returns the API response dict or None on error.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_str}/{end_str}"

    try:
        response = get(
            url,
            params={
                "adjusted": "true",
                "sort": "asc",
                "limit": 120,
                "apiKey": token,
            },
            timeout=3.0,
        ).json()
        return response if response.get("status") in ["OK", "DELAYED"] else None
    except HTTPError:
        return None


class SXNGPlugin(Plugin):
    """Show a small stock price chart for likely security identifiers.

    The plugin runs on the first page only and silently no-ops if the query
    doesn't look like a security identifier or when Finnhub isn't configured.
    """

    id = "stock_chart"

    def __init__(self, plg_cfg: PluginCfg) -> None:
        super().__init__(plg_cfg)

        # Plugin no longer uses server-side configuration
        # All settings are now user preferences only
        self.token: str | None = None
        self.timeframe_days: int = 30

        self.info = PluginInfo(
            id=self.id,
            name=gettext("Stock chart"),
            description=gettext("Show a small historical price chart using Polygon.io."),
            preference_section="query",
        )

        # Pre-compiled regex to quickly skip queries that cannot be identifiers
        self._quick_accept = re.compile(r"^[A-Za-z0-9 .\-]{1,20}$")

    def init(self, app) -> bool:
        """Initialize plugin. Always enabled since users can provide their own token."""
        return True

    def post_search(self, request: SXNG_Request, search: SearchWithPlugins) -> EngineResults:
        """Produce a stock chart answer when the query looks like a security.

        Parameters
        ----------
        request : SXNG_Request
            The incoming request context.
        search : SearchWithPlugins
            The current search instance.

        Returns
        -------
        EngineResults
            A possibly empty results list containing at most one chart answer.
        """
        results = EngineResults()

        # Early validation checks
        if (
            search.search_query.pageno > 1
            or not (token := request.preferences.get_value("stock_chart_token"))
            or not (raw_q := search.search_query.query)
            or not self._quick_accept.match(raw_q)
            or not (ident := _normalize_identifier(raw_q))
        ):
            return results

        # Get timeframe preference with default
        timeframe_days = request.preferences.get_value("stock_chart_timeframe") or 7

        # Use the identifier directly as the symbol for Polygon.io
        symbol = ident.upper()

        # Fetch stock data from Polygon.io
        data = _fetch_polygon_data(symbol, token, timeframe_days)
        if not data or not (results_data := data.get("results")):
            return results

        # Extract close prices and timestamps
        closes = [float(item["c"]) for item in results_data]
        times = [int(item["t"]) for item in results_data]

        if not closes or not times:
            return results

        last_price = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else None

        answer = StockChartAnswer(
            symbol=symbol,
            name=symbol,  # Polygon doesn't provide company name
            last_price=last_price,
            previous_close=prev_close,
            closes=closes,
            times=times,
            currency="USD",  # Polygon typically returns USD data
            url=None,
            timeframe_days=timeframe_days,
            market_data=results_data,
        )

        results.add(answer)
        return results
