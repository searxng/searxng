# SPDX-License-Identifier: AGPL-3.0-or-later
"""Processor used for ``online_url_search`` engines."""

import typing as t
import re

from .online import OnlineProcessor, OnlineParams

if t.TYPE_CHECKING:
    from .abstract import EngineProcessor
    from searx.search.models import SearchQuery


search_syntax = {
    "http": re.compile(r"https?:\/\/[^ ]*"),
    "ftp": re.compile(r"ftps?:\/\/[^ ]*"),
    "data:image": re.compile("data:image/[^; ]*;base64,[^ ]*"),
}
"""Search syntax used for a URL search."""


class UrlParams(t.TypedDict):
    """URL request parameters."""

    search_urls: dict[str, str | None]


class OnlineUrlSearchParams(UrlParams, OnlineParams):  # pylint: disable=duplicate-bases
    """Request parameters of a ``online_url_search`` engine."""


class OnlineUrlSearchProcessor(OnlineProcessor):
    """Processor class used by ``online_url_search`` engines."""

    engine_type: str = "online_url_search"

    def get_params(self, search_query: "SearchQuery", engine_category: str) -> OnlineUrlSearchParams | None:
        """Returns a dictionary with the :ref:`request params <engine request
        online_currency>` (:py:obj:`OnlineUrlSearchParams`).  ``None`` is
        returned if the search query does not match :py:obj:`search_syntax`."""

        online_params: OnlineParams | None = super().get_params(search_query, engine_category)
        if online_params is None:
            return None

        search_urls: dict[str, str | None] = {}
        has_match: bool = False

        for url_schema, url_re in search_syntax.items():
            search_urls[url_schema] = None
            m = url_re.search(search_query.query)
            if m:
                has_match = True
                search_urls[url_schema] = m[0]

        if not has_match:
            return None

        params: OnlineUrlSearchParams = {
            **online_params,
            "search_urls": search_urls,
        }

        return params
