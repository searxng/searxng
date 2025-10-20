# SPDX-License-Identifier: AGPL-3.0-or-later
"""Simple implementation to store TrackerPatterns data in a SQL database."""
# pylint: disable=too-many-branches

import typing as t

__all__ = ["TrackerPatternsDB"]

import re
from collections.abc import Iterator
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from httpx import HTTPError

from searx.data.core import get_cache, log
from searx.network import get as http_get

if t.TYPE_CHECKING:
    from searx.cache import CacheRowType


RuleType = tuple[str, list[str], list[str]]


@t.final
class TrackerPatternsDB:
    # pylint: disable=missing-class-docstring

    ctx_name = "data_tracker_patterns"

    CLEAR_LIST_URL = [
        # ClearURL rule lists, the first one that responds HTTP 200 is used
        "https://rules1.clearurls.xyz/data.minify.json",
        "https://rules2.clearurls.xyz/data.minify.json",
        "https://raw.githubusercontent.com/ClearURLs/Rules/refs/heads/master/data.min.json",
    ]

    class Fields:
        # pylint: disable=too-few-public-methods, invalid-name
        url_regexp: t.Final = 0  # URL (regular expression) match condition of the link
        url_ignore: t.Final = 1  # URL (regular expression) to ignore
        del_args: t.Final = 2  # list of URL arguments (regular expression) to delete

    def __init__(self):
        self.cache = get_cache()

    def init(self):
        if self.cache.properties("tracker_patterns loaded") != "OK":
            # To avoid parallel initializations, the property is set first
            self.cache.properties.set("tracker_patterns loaded", "OK")
            self.load()
        # F I X M E:
        #     do we need a maintenance .. remember: database is stored
        #     in /tmp and will be rebuild during the reboot anyway

    def load(self):
        log.debug("init searx.data.TRACKER_PATTERNS")
        rows: "list[CacheRowType]" = []

        for rule in self.iter_clear_list():
            key = rule[self.Fields.url_regexp]
            value = (
                rule[self.Fields.url_ignore],
                rule[self.Fields.del_args],
            )
            rows.append((key, value, None))

        self.cache.setmany(rows, ctx=self.ctx_name)

    def add(self, rule: RuleType):
        key = rule[self.Fields.url_regexp]
        value = (
            rule[self.Fields.url_ignore],
            rule[self.Fields.del_args],
        )
        self.cache.set(key=key, value=value, ctx=self.ctx_name, expire=None)

    def rules(self) -> Iterator[RuleType]:
        self.init()
        for key, value in self.cache.pairs(ctx=self.ctx_name):
            yield key, value[0], value[1]

    def iter_clear_list(self) -> Iterator[RuleType]:
        resp = None
        for url in self.CLEAR_LIST_URL:
            log.debug("TRACKER_PATTERNS: Trying to fetch %s...", url)
            try:
                resp = http_get(url, timeout=3)

            except HTTPError as exc:
                log.warning("TRACKER_PATTERNS: HTTPError (%s) occured while fetching %s", url, exc)
                continue

            if resp.status_code != 200:
                log.warning(f"TRACKER_PATTERNS: ClearURL ignore HTTP {resp.status_code} {url}")
                continue

            break

        if resp is None:
            log.error("TRACKER_PATTERNS: failed fetching ClearURL rule lists")
            return

        for rule in resp.json()["providers"].values():
            yield (
                rule["urlPattern"].replace("\\\\", "\\"),  # fix javascript regex syntax
                [exc.replace("\\\\", "\\") for exc in rule.get("exceptions", [])],
                rule.get("rules", []),
            )

    def clean_url(self, url: str) -> bool | str:
        """The URL arguments are normalized and cleaned of tracker parameters.

        Returns bool ``True`` to use URL unchanged (``False`` to ignore URL).
        If URL should be modified, the returned string is the new URL to use.
        """

        new_url = url
        parsed_new_url = urlparse(url=new_url)

        for rule in self.rules():

            query_str: str = parsed_new_url.query
            if not query_str:
                # There are no more query arguments in the parsed_new_url on
                # which rules can be applied, stop iterating over the rules.
                break

            if not re.match(rule[self.Fields.url_regexp], new_url):
                # no match / ignore pattern
                continue

            do_ignore = False
            for pattern in rule[self.Fields.url_ignore]:
                if re.match(pattern, new_url):
                    do_ignore = True
                    break

            if do_ignore:
                # pattern is in the list of exceptions / ignore pattern
                # HINT:
                #    we can't break the outer pattern loop since we have
                #    overlapping urlPattern like ".*"
                continue

            query_args: list[tuple[str, str]] = list(parse_qsl(parsed_new_url.query))
            if query_args:
                # remove tracker arguments from the url-query part
                for name, val in query_args.copy():
                    # remove URL arguments
                    for pattern in rule[self.Fields.del_args]:
                        if re.match(pattern, name):
                            log.debug(
                                "TRACKER_PATTERNS: %s remove tracker arg: %s='%s'", parsed_new_url.netloc, name, val
                            )
                            query_args.remove((name, val))

                parsed_new_url = parsed_new_url._replace(query=urlencode(query_args))
                new_url = urlunparse(parsed_new_url)

            else:
                # The query argument for URLs like:
                # - 'http://example.org?q='       --> query_str is 'q=' and query_args is []
                # - 'http://example.org?/foo/bar' --> query_str is 'foo/bar' and  query_args is []
                # is a simple string and not a key/value dict.
                for pattern in rule[self.Fields.del_args]:
                    if re.match(pattern, query_str):
                        log.debug("TRACKER_PATTERNS: %s remove tracker arg: '%s'", parsed_new_url.netloc, query_str)
                        parsed_new_url = parsed_new_url._replace(query="")
                        new_url = urlunparse(parsed_new_url)
                        break

        if new_url != url:
            return new_url

        return True


if __name__ == "__main__":
    db = TrackerPatternsDB()
    for r in db.rules():
        print(r)
