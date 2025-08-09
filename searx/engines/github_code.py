# SPDX-License-Identifier: AGPL-3.0-or-later
"""Github Code Search (IT)

.. _Github REST API for code search:
    https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-code
.. _Github REST API auth for code search:
    https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-code--fine-grained-access-tokens

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`ghc_auth`
  Change the authentication method used when using the API, defaults to none.

Optional settings are:

- :py:obj:`ghc_highlight_matching_lines`
   Control the highlighing of the matched text (turns off/on).
- :py:obj:`ghc_strip_new_lines`
   Strip new lines at the start or end of each code fragment.
- :py:obj:`ghc_strip_whitespace`
   Strip any whitespace at the start or end of each code fragment.
- :py:obj:`ghc_insert_block_separator`
   Add a `...` between each code fragment before merging them.

.. code:: yaml

  - name: github code
    engine: github_code
    shortcut: ghc
    ghc_auth:
      type: "none"

  - name: github code
    engine: github_code
    shortcut: ghc
    ghc_auth:
      type: "personal_access_token"
      token: "<token>"
    ghc_highlight_matching_lines: true
    ghc_strip_whitespace: true
    ghc_strip_new_lines: true


  - name: github code
    engine: github_code
    shortcut: ghc
    ghc_auth:
      type: "bearer"
      token: "<token>"

Implementation
===============

Github does not return the code linex indices alongside the code fragment in the
search API. Since these are not super important for the user experience all the
code lines are just relabeled (starting from 1) and appended (a disjoint set of
code blocks in a single file might be returned from the API).
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode, urlparse

from pygments.lexers import find_lexer_class_for_filename
from searx.result_types import EngineResults

# about
about = {
    "website": 'https://github.com/',
    "wikidata_id": 'Q364',
    "official_api_documentation": 'https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-code',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ['code']


search_url = 'https://api.github.com/search/code?sort=indexed&{query}&{page}'
# https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#text-match-metadata
accept_header = 'application/vnd.github.text-match+json'
paging = True

ghc_auth = {
    "type": "none",
    "token": "",
}
"""Change the method of authenticating to the github API.

``type`` needs to be one of ``none``, ``personal_access_token``, or ``bearer``.
When type is not `none` a token is expected to be passed as well in
``auth.token``.

If there is any privacy concerns about generating a token, one can use the API
without authentication.  The calls will be heavily rate limted, this is what the
API returns on such calls::

    API rate limit exceeded for <redacted ip>.
    (But here's the good news: Authenticated requests get a higher rate limit)

The personal access token or a bearer for an org or a group can be generated [in
the `Github settings`_.

.. _Github settings:
   https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-code--fine-grained-access-tokens
"""

ghc_highlight_matching_lines = True
"""Highlight the matching code lines."""

ghc_strip_new_lines = True
"""Strip leading and trailing newlines for each returned fragment.
Single file might return multiple code fragments.
"""

ghc_strip_whitespace = False
"""Strip all leading and trailing whitespace for each returned fragment.
Single file might return multiple code fragments. Enabling this might break
code indentation.
"""

ghc_api_version = "2022-11-28"
"""The version of the Github REST API.
"""

ghc_insert_block_separator = False
"""Each file possibly consists of more than one code block that matches the
search, if this is set to true, the blocks will be separated with `...` line.
This might break the lexer and thus result in the lack of code highlighting.
"""


def request(query, params):

    params['url'] = search_url.format(query=urlencode({'q': query}), page=urlencode({'page': params['pageno']}))
    params['headers']['Accept'] = accept_header
    params['headers']['X-GitHub-Api-Version'] = ghc_api_version

    if ghc_auth['type'] == "none":
        # Without the auth header the query fails, so add a dummy instead.
        # Queries without auth are heavily rate limited.
        params['headers']['Authorization'] = "placeholder"
    if ghc_auth['type'] == "personal_access_token":
        params['headers']['Authorization'] = f"token {ghc_auth['token']}"
    if ghc_auth['type'] == "bearer":
        params['headers']['Authorization'] = f"Bearer {ghc_auth['token']}"

    return params


def get_code_language_name(filename: str, code_snippet: str) -> Optional[str]:
    """
    Returns a code language name by pulling information from
    the filename if possible otherwise by scanning the passed code
    snippet. In case there is any parsing error just default to no syntax
    highlighting.
    """
    try:
        lexer = find_lexer_class_for_filename(filename, code=code_snippet)
        if lexer is None:
            return None
        code_name_aliases = lexer.aliases
        if len(code_name_aliases) == 0:
            return None
        return code_name_aliases[0]
    except Exception:  # pylint: disable=broad-except
        return None


def extract_code(code_matches) -> tuple[list[str], set[int]]:
    """
    Iterate over multiple possible matches, for each extract a code fragment.
    Github additionally sends context for _word_ highlights; pygments supports
    highlighting lines, as such we calculate which lines to highlight while
    traversing the text.
    """
    lines = []
    highlighted_lines_index = set()

    for i, match in enumerate(code_matches):
        if i > 0 and ghc_insert_block_separator:
            lines.append("...")
        buffer = []
        highlight_groups = [highlight_group['indices'] for highlight_group in match['matches']]

        code = match['fragment']
        original_code_lenght = len(code)

        if ghc_strip_whitespace:
            code = code.lstrip()
        if ghc_strip_new_lines:
            code = code.lstrip("\n")

        offset = original_code_lenght - len(code)

        if ghc_strip_whitespace:
            code = code.rstrip()
        if ghc_strip_new_lines:
            code = code.rstrip("\n")

        for i, letter in enumerate(code):
            if len(highlight_groups) > 0:
                # the API ensures these are sorted already, and we have a
                # guarateed match in the code (all indices are in the range 0
                # and len(fragment)), so only check the first
                # highlight group
                [after, before] = highlight_groups[0]
                if after <= (i + offset) < before:
                    # pygments enumerates lines from 1, highlight the next line
                    highlighted_lines_index.add(len(lines) + 1)
                    highlight_groups.pop(0)

            if letter == "\n":
                lines.append("".join(buffer))
                buffer = []
                continue

            buffer.append(letter)
        lines.append("".join(buffer))
    return lines, highlighted_lines_index


def response(resp) -> EngineResults:
    results = EngineResults()

    for item in resp.json().get('items', []):
        repo = item['repository']
        text_matches = item['text_matches']
        # ensure picking only the code contents in the blob
        code_matches = [
            match for match in text_matches if match["object_type"] == "FileContent" and match["property"] == "content"
        ]
        lines, highlighted_lines_index = extract_code(code_matches)
        if not ghc_highlight_matching_lines:
            highlighted_lines_index = set()

        code_snippet = "\n".join(lines)

        kwargs = {
            'template': 'code.html',
            'url': item['html_url'],
            'title': f"{repo['full_name']} · {item['path']}",
            'content': repo['description'],
            'repository': repo['html_url'],
            'codelines': [(i + 1, line) for (i, line) in enumerate(lines)],
            'hl_lines': highlighted_lines_index,
            'code_language': get_code_language_name(filename=item['name'], code_snippet=code_snippet),
            # important to set for highlighing
            'strip_whitespace': ghc_strip_whitespace,
            'strip_new_lines': ghc_strip_new_lines,
            'parsed_url': urlparse(item['html_url']),
        }
        results.add(results.types.LegacyResult(**kwargs))

    return results
