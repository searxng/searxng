# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-class-docstring
from __future__ import annotations
import typing

import re
import hashlib

from flask_babel import gettext

from searx.plugins import Plugin, PluginInfo
from searx.result_types import EngineResults

if typing.TYPE_CHECKING:
    from searx.search import SearchWithPlugins
    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg


class SXNGPlugin(Plugin):
    """Plugin converts strings to different hash digests.  The results are
    displayed in area for the "answers".
    """

    id = "hash_plugin"
    keywords = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]

    def __init__(self, plg_cfg: "PluginCfg") -> None:
        super().__init__(plg_cfg)

        self.parser_re = re.compile(f"({'|'.join(self.keywords)}) (.*)", re.I)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Hash plugin"),
            description=gettext(
                "Converts strings to different hash digests. Available functions: md5, sha1, sha224, sha256, sha384, sha512."  # pylint:disable=line-too-long
            ),
            examples=["sha512 The quick brown fox jumps over the lazy dog"],
            preference_section="query",
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        """Returns a result list only for the first page."""
        results = EngineResults()

        if search.search_query.pageno > 1:
            return results

        m = self.parser_re.match(search.search_query.query)
        if not m:
            # wrong query
            return results

        function, string = m.groups()
        if not string.strip():
            # end if the string is empty
            return results

        # select hash function
        f = hashlib.new(function.lower())

        # make digest from the given string
        f.update(string.encode("utf-8").strip())
        answer = function + " " + gettext("hash digest") + ": " + f.hexdigest()

        results.add(results.types.Answer(answer=answer))

        return results
