# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring
from __future__ import annotations
import typing

import re
from urllib.parse import parse_qsl

from flask_babel import gettext
from searx import get_setting
from searx.plugins import Plugin, PluginInfo
from searx.extended_types import sxng_request

from ._core import log

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.result_types import Result, LegacyResult
    from searx.plugins import PluginCfg


ahmia_blacklist: list = []


def filter_url_field(result: "Result|LegacyResult", field_name: str, url_src: str) -> bool | str:
    """Returns bool ``True`` to use URL unchanged (``False`` to ignore URL).
    If URL should be modified, the returned string is the new URL to use."""

    if field_name != "url":
        return True  # use it unchanged

    doi = extract_doi(result.parsed_url)
    if doi and len(doi) < 50:
        for suffix in ("/", ".pdf", ".xml", "/full", "/meta", "/abstract"):
            doi = doi.removesuffix(suffix)
        new_url = get_doi_resolver() + doi
        if "doi" not in result:
            result["doi"] = doi
        log.debug("oa_doi_rewrite: [URL field: %s] %s -> %s", field_name, url_src, new_url)
        return new_url  # use new url

    return True  # use it unchanged


class SXNGPlugin(Plugin):
    """Avoid paywalls by redirecting to open-access."""

    id = "oa_doi_rewrite"

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Open Access DOI rewrite"),
            description=gettext("Avoid paywalls by redirecting to open-access versions of publications when available"),
            preference_section="general",
        )

    def on_result(
        self,
        request: "SXNG_Request",
        search: "SearchWithPlugins",
        result: "Result",
    ) -> bool:  # pylint: disable=unused-argument
        if result.parsed_url:
            result.filter_urls(filter_url_field)
        return True


regex = re.compile(r'10\.\d{4,9}/[^\s]+')


def extract_doi(url):
    m = regex.search(url.path)
    if m:
        return m.group(0)
    for _, v in parse_qsl(url.query):
        m = regex.search(v)
        if m:
            return m.group(0)
    return None


def get_doi_resolver() -> str:
    doi_resolvers = get_setting("doi_resolvers")
    selected_resolver = sxng_request.preferences.get_value('doi_resolver')[0]
    if selected_resolver not in doi_resolvers:
        selected_resolver = get_setting("default_doi_resolver")
    return doi_resolvers[selected_resolver]
