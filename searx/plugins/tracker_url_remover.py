# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, unused-argument

from __future__ import annotations
import typing

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from flask_babel import gettext

from searx.data import TRACKER_PATTERNS

from . import Plugin, PluginInfo
from ._core import log

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result, LegacyResult
    from searx.plugins import PluginCfg


class SXNGPlugin(Plugin):
    """Remove trackers arguments from the returned URL."""

    id = "tracker_url_remover"
    log = log.getChild(id)

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Tracker URL remover"),
            description=gettext("Remove trackers arguments from the returned URL"),
            preference_section="privacy",
        )

    def on_result(self, request: "SXNG_Request", search: "SearchWithPlugins", result: Result) -> bool:

        result.filter_urls(self.filter_url_field)
        return True

    @classmethod
    def filter_url_field(cls, result: "Result|LegacyResult", field_name: str, url_src: str) -> bool | str:
        """Returns bool ``True`` to use URL unchanged (``False`` to ignore URL).
        If URL should be modified, the returned string is the new URL to use."""

        if not url_src:
            cls.log.debug("missing a URL in field %s", field_name)
            return True

        new_url = url_src
        parsed_new_url = urlparse(url=new_url)

        for rule in TRACKER_PATTERNS:

            if not re.match(rule["urlPattern"], new_url):
                # no match / ignore pattern
                continue

            in_exceptions = False
            for exception in rule["exceptions"]:
                if re.match(exception, new_url):
                    in_exceptions = True
                    break
            if in_exceptions:
                # pattern is in the list of exceptions / ignore pattern
                # hint: we can't break the outer pattern loop since we have
                # overlapping urlPattern like ".*"
                continue

            # remove tracker arguments from the url-query part
            query_args: list[tuple[str, str]] = list(parse_qsl(parsed_new_url.query))

            for name, val in query_args.copy():
                for reg in rule["trackerParams"]:
                    if re.match(reg, name):
                        cls.log.debug("%s remove tracker arg: %s='%s'", parsed_new_url.netloc, name, val)
                        query_args.remove((name, val))

            parsed_new_url = parsed_new_url._replace(query=urlencode(query_args))
            new_url = urlunparse(parsed_new_url)

        if new_url != url_src:
            return new_url

        return True
