# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-few-public-methods
"""Parser subset for the Easylist syntax.

This implementation does NOT support using regular expressions or content filters.

.. seealso:

   `Adblock Plus guide about the EasyList syntax <https://help.eyeo.com/en/adblockplus/how-to-write-filters>`_

   `uBlock origin about the syntax <https://github.com/gorhill/ublock/wiki/static-filter-syntax>`_

   `Adguard guide about creating filters <https://adguard.com/kb/general/ad-filtering/create-own-filters/>`_
"""

import re

import fnmatch
import urllib.parse
from enum import Enum

_NON_SEPARATOR_CHARACTERS = r"a-z0-9_.%\-"
"""
Characters that may not be matched by the separator wildcard ``^``.

For example, ``example.com^`` matches "example.com/foo", but not "example.commercial".
"""


class EasylistFilterParserException(Exception):
    """Exception thrown when :ref:`parse` fails to execute."""


class EasylistFilterWildcardType(Enum):
    """
    Described how the start/end of the glob should be matched.
    """

    WILDCARD = 1
    """
    Any characters may precede/come after the glob.
    """
    FULL_URL_EXACT = 3
    """
    Glob matches the full start of the URL.
    """
    DOMAIN_START_EXACT = 2
    """
    Start matching at the domain start of the URL.

    This means that the subdomain has to match as well.
    """


class EasylistFilterRule:
    """
    This represents a parsed Easylist filter rule.
    """

    is_exception: bool = False
    """
    Exception rules are rules that allow a website to be visited.

    For example, if one rule blocks ``||example.com``, the rule ``@@||foo.example.com`` unblocks the "foo" subdomain.
    """

    extra_options: list[str] = []
    """
    List of extra options that should be followed for matching this domain, e.g. ["document", "redirect=noopframe"].
    """

    filter_glob: str = ""
    """
    A `fnmatch <https://docs.python.org/3/library/fnmatch.html>`_-compatible glob used for filtering if a URL matches.

    E.g. ``http*ample.com*`` would match *https://example.com*, *http://example.com/foo*, ...
    """

    start_wildcard_type: EasylistFilterWildcardType = EasylistFilterWildcardType.WILDCARD
    """
    How the start of the pattern should be matched.

    Also see :py:obj:`EasylistFilterRule.end_wildcard_type`.
    """

    end_wildcard_type: EasylistFilterWildcardType = EasylistFilterWildcardType.WILDCARD
    """
    How the end of the pattern should be matched.

    For example, ``svg|`` only matches URLs ending with "svg" like *https://example.com/logo.svg*,
    but not URLs that contain "svg" in other places of the URL, such as *https://foo.svg/bar*.

    Also see :py:obj:`EasylistFilterRule.start_wildcard_type`.
    """

    _compiled_regex: re.Pattern[str] | None = None
    """
    This is the compiled Regex version of :py:obj:``EasylistFilterRule.filter_glob``, with respect to
    :py:obj:`EasylistFilterRule.start_wildcard_type` end :py:obj:`EasylistFilterRule.end_wildcard_type`.

    This is used to cache the Regex to improve performance by >10x because compiling regular expressions
    is very expensive.
    """

    # __eq__ and __hash__ are override for HashSet compatibility in blocklists.py
    # both implementations ignore EasylistFilterRule.extra_options, as they're not
    # relevant for our context (simply blocking URLs)
    def __eq__(self, other):
        if not isinstance(other, EasylistFilterRule):
            return False

        return (
            self.filter_glob == other.filter_glob
            and self.start_wildcard_type == other.start_wildcard_type
            and self.end_wildcard_type == other.end_wildcard_type
            and self.is_exception == other.is_exception
        )

    def __hash__(self):
        return hash((self.filter_glob, self.start_wildcard_type, self.end_wildcard_type, self.is_exception))

    def matches_url(self, url: urllib.parse.ParseResult) -> bool:
        """
        Check whether this :py:obj:`EasylistFilterRule` matches the given `url`.

        The URL is matched case insensitively.
        """

        glob = self.filter_glob.lower()
        to_match = url.geturl().lower()

        if self.start_wildcard_type == EasylistFilterWildcardType.WILDCARD:
            glob = f"*{glob}"
        elif self.start_wildcard_type == EasylistFilterWildcardType.DOMAIN_START_EXACT:
            # remove everything before the domain
            scheme = f"{url.scheme.lower()}://"
            to_match = to_match.removeprefix(scheme)

        # exact domain is only support for the start of the pattern
        # so there's no else case here
        if self.end_wildcard_type == EasylistFilterWildcardType.WILDCARD:
            glob = f"{glob}*"

        # check if the regex was already compiled - if not, compile it now
        if not self._compiled_regex:
            # compile the glob string to a regular expression string
            glob_re = fnmatch.translate(glob)
            # cache the regex for future use
            self._compiled_regex = re.compile(glob_re)

        return self._compiled_regex.fullmatch(to_match) is not None


def parse(line: str) -> EasylistFilterRule | None:
    """
    Parser a line into an Easylist filter rule.

    Throws a :py:obj:`EasylistFilterParserException` if parsing fails.
    """
    line = line.strip()

    if not line or line.startswith("!") or line.startswith("["):
        # comment found, i.e. not a filter rule
        return None

    rule = EasylistFilterRule()

    remaining = line
    has_pattern_started = False
    while len(remaining):
        if remaining.startswith("@@"):
            rule.is_exception = True
            remaining = remaining[2:]
        elif remaining.startswith("||"):
            if has_pattern_started:
                raise EasylistFilterParserException("`||` may only be used at the start of the rule")

            rule.start_wildcard_type = EasylistFilterWildcardType.DOMAIN_START_EXACT
            remaining = remaining[2:]
        elif remaining.startswith("|"):
            if has_pattern_started:
                rule.end_wildcard_type = EasylistFilterWildcardType.FULL_URL_EXACT
            else:
                rule.start_wildcard_type = EasylistFilterWildcardType.FULL_URL_EXACT
            remaining = remaining[1:]
        elif remaining.startswith("$"):
            rule.extra_options = remaining[1:].split(",")
            remaining = ""  # extra options are always the last part of the URL
        else:
            # progress by one single character - this is not very clean, but it avoids
            # doing complex regex operations which would slow down execution times
            rule.filter_glob += remaining[0]
            has_pattern_started = True
            remaining = remaining[1:]

    if not rule.filter_glob:
        # this could be a rule like `$all,domain=example.com|example.org`, but we don't support that
        return None

    # this ensures compatibility with fnmatch, see https://docs.python.org/3/library/fnmatch.html
    rule.filter_glob = rule.filter_glob.replace("^", f"[!{_NON_SEPARATOR_CHARACTERS}]")
    return rule
