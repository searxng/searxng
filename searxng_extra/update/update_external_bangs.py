#!/usr/bin/env python
# lint: pylint
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Update :origin:`searx/data/external_bangs.json` using the duckduckgo bangs
(:origin:`CI Update data ... <.github/workflows/data-update.yml>`).

https://duckduckgo.com/newbang loads:

* a javascript which provides the bang version ( https://duckduckgo.com/bv1.js )
* a JSON file which contains the bangs ( https://duckduckgo.com/bang.v260.js for example )

This script loads the javascript, then the bangs.

The javascript URL may change in the future ( for example
https://duckduckgo.com/bv2.js ), but most probably it will requires to update
RE_BANG_VERSION

"""
# pylint: disable=C0116

import json
import re
from os.path import join

import httpx

from searx import searx_dir  # pylint: disable=E0401 C0413
from searx.external_bang import LEAF_KEY

# from https://duckduckgo.com/newbang
URL_BV1 = 'https://duckduckgo.com/bv1.js'
RE_BANG_VERSION = re.compile(r'\/bang\.v([0-9]+)\.js')
HTTPS_COLON = 'https:'
HTTP_COLON = 'http:'


def get_bang_url():
    response = httpx.get(URL_BV1)
    response.raise_for_status()

    r = RE_BANG_VERSION.findall(response.text)
    return f'https://duckduckgo.com/bang.v{r[0]}.js', r[0]


def fetch_ddg_bangs(url):
    response = httpx.get(url)
    response.raise_for_status()
    return json.loads(response.content.decode())


def merge_when_no_leaf(node):
    """Minimize the number of nodes

    ``A -> B -> C``

    - ``B`` is child of ``A``
    - ``C`` is child of ``B``

    If there are no ``C`` equals to ``<LEAF_KEY>``, then each ``C`` are merged
    into ``A``.  For example (5 nodes)::

      d -> d -> g -> <LEAF_KEY> (ddg)
        -> i -> g -> <LEAF_KEY> (dig)

    becomes (3 noodes)::

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


def get_bangs_filename():
    return join(join(searx_dir, "data"), "external_bangs.json")


if __name__ == '__main__':
    bangs_url, bangs_version = get_bang_url()
    print(f'fetch bangs from {bangs_url}')
    output = {'version': bangs_version, 'trie': parse_ddg_bangs(fetch_ddg_bangs(bangs_url))}
    with open(get_bangs_filename(), 'w', encoding="utf8") as fp:
        json.dump(output, fp, ensure_ascii=False, indent=4)
