# -*- mode: python -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A SearXNG message file, see :py:obj:`searx.babel`
"""

from searx import webutils
from searx import engines

__all__ = [
    'CONSTANT_NAMES',
    'CATEGORY_NAMES',
    'CATEGORY_GROUPS',
    'STYLE_NAMES',
]

CONSTANT_NAMES = {
    # Constants defined in other modules
    'DEFAULT_GROUP_NAME': webutils.DEFAULT_GROUP_NAME,
    'OTHER_CATEGORY': engines.OTHER_CATEGORY,
}

CATEGORY_NAMES = {
    'FILES': 'files',
    'GENERAL': 'general',
    'MUSIC': 'music',
    'SOCIAL_MEDIA': 'social media',
    'IMAGES': 'images',
    'VIDEOS': 'videos',
    'IT': 'it',
    'NEWS': 'news',
    'MAP': 'map',
    'ONIONS': 'onions',
    'SCIENCE': 'science',
}

CATEGORY_GROUPS = {
    # non-tab categories
    'APPS': 'apps',
    'DICTIONARIES': 'dictionaries',
    'LYRICS': 'lyrics',
    'PACKAGES': 'packages',
    'Q_A': 'q&a',
    'REPOS': 'repos',
    'SOFTWARE_WIKIS': 'software wikis',
    'WEB': 'web',
}

STYLE_NAMES = {
    'AUTO': 'auto',
    'LIGHT': 'light',
    'DARK': 'dark',
}
