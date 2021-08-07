# SPDX-License-Identifier: AGPL-3.0-or-later

import typing
import re


from yarl import URL


class URLPattern:
    """
    A utility class currently used for making lookups against proxy keys...
    # Wildcard matching...
    >>> pattern = URLPattern("all")
    >>> pattern.matches(yarl.URL("http://example.com"))
    True
    # Witch scheme matching...
    >>> pattern = URLPattern("https")
    >>> pattern.matches(yarl.URL("https://example.com"))
    True
    >>> pattern.matches(yarl.URL("http://example.com"))
    False
    # With domain matching...
    >>> pattern = URLPattern("https://example.com")
    >>> pattern.matches(yarl.URL("https://example.com"))
    True
    >>> pattern.matches(yarl.URL("http://example.com"))
    False
    >>> pattern.matches(yarl.URL("https://other.com"))
    False
    # Wildcard scheme, with domain matching...
    >>> pattern = URLPattern("all://example.com")
    >>> pattern.matches(yarl.URL("https://example.com"))
    True
    >>> pattern.matches(yarl.URL("http://example.com"))
    True
    >>> pattern.matches(yarl.URL("https://other.com"))
    False
    # With port matching...
    >>> pattern = URLPattern("https://example.com:1234")
    >>> pattern.matches(yarl.URL("https://example.com:1234"))
    True
    >>> pattern.matches(yarl.URL("https://example.com"))
    False
    """

    def __init__(self, pattern: str) -> None:
        if pattern and ":" not in pattern:
            raise ValueError(
                f"Proxy keys should use proper URL forms rather "
                f"than plain scheme strings. "
                f'Instead of "{pattern}", use "{pattern}://"'
            )

        url = URL(pattern)
        self.pattern = pattern
        self.scheme = "" if url.scheme == "all" else url.scheme
        self.host = "" if url.host == "*" else url.host
        self.port = url.port
        if not url.host or url.host == "*":
            self.host_regex: typing.Optional[typing.Pattern[str]] = None
        else:
            if url.host.startswith("*."):
                # *.example.com should match "www.example.com", but not "example.com"
                domain = re.escape(url.host[2:])
                self.host_regex = re.compile(f"^.+\\.{domain}$")
            elif url.host.startswith("*"):
                # *example.com should match "www.example.com" and "example.com"
                domain = re.escape(url.host[1:])
                self.host_regex = re.compile(f"^(.+\\.)?{domain}$")
            else:
                # example.com should match "example.com" but not "www.example.com"
                domain = re.escape(url.host)
                self.host_regex = re.compile(f"^{domain}$")

    def matches(self, other: URL) -> bool:
        if self.scheme and self.scheme != other.scheme:
            return False
        if (
            self.host
            and self.host_regex is not None
            and not self.host_regex.match(other.host or '')
        ):
            return False
        if self.port is not None and self.port != other.port:
            return False
        return True

    @property
    def priority(self) -> tuple:
        """
        The priority allows URLPattern instances to be sortable, so that
        we can match from most specific to least specific.
        """
        # URLs with a port should take priority over URLs without a port.
        port_priority = 0 if self.port is not None else 1
        # Longer hostnames should match first.
        host_priority = -len(self.host or '')
        # Longer schemes should match first.
        scheme_priority = -len(self.scheme)
        return (port_priority, host_priority, scheme_priority)

    def __hash__(self) -> int:
        return hash(self.pattern)

    def __lt__(self, other: "URLPattern") -> bool:
        return self.priority < other.priority

    def __eq__(self, other: typing.Any) -> bool:
        return isinstance(other, URLPattern) and self.pattern == other.pattern

    def __repr__(self) -> str:
        return f"<URLPattern pattern=\"{self.pattern}\">"
