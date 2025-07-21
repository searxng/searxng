#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Update :origin:`searx/data/external_bangs.json` using the duckduckgo bangs
from :py:obj:`BANGS_URL`.

- :origin:`CI Update data ... <.github/workflows/data-update.yml>`

"""

import json

from searx.external_bang import LEAF_KEY
from searx.data import data_dir
from searx.network import get as http_get

DATA_FILE = data_dir / 'external_bangs.json'

BANGS_URL = 'https://duckduckgo.com/bang.js'
"""JSON file which contains the bangs."""

HTTPS_COLON = 'https:'
HTTP_COLON = 'http:'


def main():
    print(f'fetch bangs from {BANGS_URL}')
    response = http_get(BANGS_URL)
    response.raise_for_status()
    ddg_bangs = json.loads(response.content.decode())
    trie = parse_ddg_bangs(ddg_bangs)
    output = {
        'version': 0,
        'trie': trie,
    }
    with DATA_FILE.open('w', encoding="utf8") as f:
        json.dump(output, f, indent=4, sort_keys=True, ensure_ascii=False)


def merge_when_no_leaf(node):
    """Minimize the number of nodes

    ``A -> B -> C``

    - ``B`` is child of ``A``
    - ``C`` is child of ``B``

    If there are no ``C`` equals to ``<LEAF_KEY>``, then each ``C`` are merged
    into ``A``.  For example (5 nodes)::

      d -> d -> g -> <LEAF_KEY> (ddg)
        -> i -> g -> <LEAF_KEY> (dig)

    becomes (3 nodes)::

      d -> dg -> <LEAF_KEY>
        -> ig -> <LEAF_KEY>

    """
    restart = False
    if not isinstance(node, dict):
        return

    # create a copy of the keys so node can be modified
    keys = list(node.keys())

    for key in keys:
        if key == LEAF_KEY:
            continue

        value = node[key]
        value_keys = list(value.keys())
        if LEAF_KEY not in value_keys:
            for value_key in value_keys:
                node[key + value_key] = value[value_key]
                merge_when_no_leaf(node[key + value_key])
            del node[key]
            restart = True
        else:
            merge_when_no_leaf(value)

    if restart:
        merge_when_no_leaf(node)


def optimize_leaf(parent, parent_key, node):
    if not isinstance(node, dict):
        return

    if len(node) == 1 and LEAF_KEY in node and parent is not None:
        parent[parent_key] = node[LEAF_KEY]
    else:
        for key, value in node.items():
            optimize_leaf(node, key, value)


def parse_ddg_bangs(ddg_bangs):
    bang_trie = {}
    bang_urls = {}

    for bang_definition in ddg_bangs:
        # bang_list
        bang_url = bang_definition['u']
        if '{{{s}}}' not in bang_url:
            # ignore invalid bang
            continue

        bang_url = bang_url.replace('{{{s}}}', chr(2))

        # only for the https protocol: "https://example.com" becomes "//example.com"
        if bang_url.startswith(HTTPS_COLON + '//'):
            bang_url = bang_url[len(HTTPS_COLON) :]

        #
        if bang_url.startswith(HTTP_COLON + '//') and bang_url[len(HTTP_COLON) :] in bang_urls:
            # if the bang_url uses the http:// protocol, and the same URL exists in https://
            # then reuse the https:// bang definition. (written //example.com)
            bang_def_output = bang_urls[bang_url[len(HTTP_COLON) :]]
        else:
            # normal use case : new http:// URL or https:// URL (without "https:", see above)
            bang_rank = str(bang_definition['r'])
            bang_def_output = bang_url + chr(1) + bang_rank
            bang_def_output = bang_urls.setdefault(bang_url, bang_def_output)

        bang_urls[bang_url] = bang_def_output

        # bang name
        bang = bang_definition['t']

        # bang_trie
        t = bang_trie
        for bang_letter in bang:
            t = t.setdefault(bang_letter, {})
        t = t.setdefault(LEAF_KEY, bang_def_output)

    # optimize the trie
    merge_when_no_leaf(bang_trie)
    optimize_leaf(None, None, bang_trie)

    return bang_trie


if __name__ == '__main__':
    main()
