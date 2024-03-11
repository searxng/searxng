# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import sys
from os import listdir
from os.path import realpath, dirname, join, isdir
from collections import defaultdict

from searx.utils import load_module

answerers_dir = dirname(realpath(__file__))


def load_answerers():
    answerers = []  # pylint: disable=redefined-outer-name

    for filename in listdir(answerers_dir):
        if not isdir(join(answerers_dir, filename)) or filename.startswith('_'):
            continue
        module = load_module('answerer.py', join(answerers_dir, filename))
        if not hasattr(module, 'keywords') or not isinstance(module.keywords, tuple) or not module.keywords:
            sys.exit(2)
        answerers.append(module)
    return answerers


def get_answerers_by_keywords(answerers):  # pylint:disable=redefined-outer-name
    by_keyword = defaultdict(list)
    for answerer in answerers:
        for keyword in answerer.keywords:
            for keyword in answerer.keywords:
                by_keyword[keyword].append(answerer.answer)
    return by_keyword


def ask(query):
    results = []
    query_parts = list(filter(None, query.query.split()))

    if not query_parts or query_parts[0] not in answerers_by_keywords:
        return results

    for answerer in answerers_by_keywords[query_parts[0]]:
        result = answerer(query)
        if result:
            results.append(result)
    return results


answerers = load_answerers()
answerers_by_keywords = get_answerers_by_keywords(answerers)
