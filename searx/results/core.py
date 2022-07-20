# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint

"""Core methods
"""
# pylint: disable=too-few-public-methods

import re
from urllib.parse import unquote
from typing import NamedTuple

from searx.engines import engines

CONTENT_LEN_IGNORED_CHARS_REGEX = re.compile(r'[,;:!?\./\\\\ ()-_]', re.M | re.U)
WHITESPACE_REGEX = re.compile('( |\t|\n)+', re.M | re.U)


class Timing(NamedTuple):  # pylint: disable=missing-class-docstring
    engine: str
    total: float
    load: float


class UnresponsiveEngine(NamedTuple):  # pylint: disable=missing-class-docstring
    engine: str
    error_type: str
    suspended: bool


def result_content_len(content):
    """Return the meaningful length of the content for a result."""
    if isinstance(content, str):
        return len(CONTENT_LEN_IGNORED_CHARS_REGEX.sub('', content))
    return 0


def result_score(result):
    weight = 1.0

    for result_engine in result['engines']:
        if hasattr(engines[result_engine], 'weight'):
            weight *= float(engines[result_engine].weight)

    occurences = len(result['positions'])

    return sum((occurences * weight) / position for position in result['positions'])


def compare_urls(url_a, url_b):
    """Lazy compare between two URL.

    "www.example.com" and "example.com" are equals.
    "www.example.com/path/" and "www.example.com/path" are equals.
    "https://www.example.com/" and "http://www.example.com/" are equals.

    Args:
        url_a (ParseResult): first URL
        url_b (ParseResult): second URL

    Returns:
        bool: True if url_a and url_b are equals
    """
    # ignore www. in comparison
    if url_a.netloc.startswith('www.'):
        host_a = url_a.netloc.replace('www.', '', 1)
    else:
        host_a = url_a.netloc
    if url_b.netloc.startswith('www.'):
        host_b = url_b.netloc.replace('www.', '', 1)
    else:
        host_b = url_b.netloc

    if host_a != host_b or url_a.query != url_b.query or url_a.fragment != url_b.fragment:
        return False

    # remove / from the end of the url if required
    path_a = url_a.path[:-1] if url_a.path.endswith('/') else url_a.path
    path_b = url_b.path[:-1] if url_b.path.endswith('/') else url_b.path

    return unquote(path_a) == unquote(path_b)
