# -*- mode: python -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A SearXNG message file, see :py:obj:`searx.babel`
"""

from searx import webutils
from searx import engines

__all__ = [
    'BRAND_CUSTOM_LINKS',
    'CATEGORY_GROUPS',
    'CATEGORY_NAMES',
    'CONSTANT_NAMES',
    'SOCIAL_MEDIA_TERMS',
    'STYLE_NAMES',
    'WEATHER_TERMS',
]

CONSTANT_NAMES = {
    # Constants defined in other modules
    'DEFAULT_CATEGORY': engines.DEFAULT_CATEGORY,
    'NO_SUBGROUPING': webutils.NO_SUBGROUPING,
}

CATEGORY_NAMES = {
    'FILES': 'files',
    'GENERAL': 'general',
    'IMAGES': 'images',
    'IT': 'it',
    'MAP': 'map',
    'MUSIC': 'music',
    'NEWS': 'news',
    'ONIONS': 'onions',
    'RADIO': 'radio',
    'SCIENCE': 'science',
    'SOCIAL_MEDIA': 'social media',
    'TV': 'tv',
    'VIDEOS': 'videos',
}

CATEGORY_GROUPS = {
    # non-tab categories
    'AI': 'ai',
    'APPS': 'apps',
    'DICTIONARIES': 'dictionaries',
    'LYRICS': 'lyrics',
    'MOVIES': 'movies',
    'PACKAGES': 'packages',
    'Q_A': 'q&a',
    'REPOS': 'repos',
    'SCIENTIFIC_PUBLICATIONS': 'scientific publications',
    'SOFTWARE_WIKIS': 'software wikis',
    'TRANSLATE': 'translate',
    'WEATHER': 'weather',
    'WEB': 'web',
    'WIKIMEDIA': 'wikimedia',
}

STYLE_NAMES = {
    'AUTO': 'auto',
    'BLACK': 'black',
    'DARK': 'dark',
    'LIGHT': 'light',
}

BRAND_CUSTOM_LINKS = {
    'ABOUT': 'About',
    'UPTIME': 'Uptime',
}

WEATHER_TERMS = {
    'AVERAGE_TEMP.': 'Average temp.',
    'CLOUD_COVER': 'Cloud cover',
    'CONDITION': 'Condition',
    'CURRENT_CONDITION': 'Current condition',
    'EVENING': 'Evening',
    'FEELS_LIKE': 'Feels like',
    'HUMIDITY': 'Humidity',
    'MAX_TEMP.': 'Max temp.',
    'MIN_TEMP.': 'Min temp.',
    'MORNING': 'Morning',
    'NIGHT': 'Night',
    'NOON': 'Noon',
    'PRESSURE': 'Pressure',
    'SUNRISE': 'Sunrise',
    'SUNSET': 'Sunset',
    'TEMPERATURE': 'Temperature',
    'UV_INDEX': 'UV index',
    'VISIBILITY': 'Visibility',
    'WIND': 'Wind',
}

SOCIAL_MEDIA_TERMS = {
    'ACTIVE_USERS': 'active users',
    'AUTHOR': 'author',
    'COMMENTS': 'comments',
    'COMMUNITY': 'community',
    'POINTS': 'points',
    'POSTS': 'posts',
    'SUBSCRIBERS': 'subscribers',
    'THREAD_ANSWERED': 'answered',
    'THREAD_CLOSED': 'closed',
    'THREAD_OPEN': 'open',
    'TITLE': 'title',
    'USER': 'user',
}
