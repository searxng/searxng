# -*- mode: python -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A SearXNG message file, see :py:obj:`searx.babel`"""

import typing

from searx import webutils
from searx import engines
from searx.weather import WeatherConditionType


__all__ = [
    'CONSTANT_NAMES',
    'CATEGORY_NAMES',
    'CATEGORY_GROUPS',
    'STYLE_NAMES',
    'BRAND_CUSTOM_LINKS',
    'WEATHER_TERMS',
    'WEATHER_CONDITIONS',
    'SOCIAL_MEDIA_TERMS',
]

CONSTANT_NAMES = {
    # Constants defined in other modules
    'NO_SUBGROUPING': webutils.NO_SUBGROUPING,
    'DEFAULT_CATEGORY': engines.DEFAULT_CATEGORY,
}

CATEGORY_NAMES = {
    'FILES': 'files',
    'GENERAL': 'general',
    'MUSIC': 'music',
    'SOCIAL_MEDIA': 'social media',
    'IMAGES': 'images',
    'VIDEOS': 'videos',
    'RADIO': 'radio',
    'TV': 'tv',
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
    'SCIENTIFIC PUBLICATIONS': 'scientific publications',
}

STYLE_NAMES = {
    'AUTO': 'auto',
    'LIGHT': 'light',
    'DARK': 'dark',
    'BLACK': 'black',
}

BRAND_CUSTOM_LINKS = {
    'UPTIME': 'Uptime',
    'ABOUT': 'About',
}

WEATHER_TERMS = {
    'AVERAGE TEMP.': 'Average temp.',
    'CLOUD COVER': 'Cloud cover',
    'CONDITION': 'Condition',
    'CURRENT CONDITION': 'Current condition',
    'EVENING': 'Evening',
    'FEELS LIKE': 'Feels like',
    'HUMIDITY': 'Humidity',
    'MAX TEMP.': 'Max temp.',
    'MIN TEMP.': 'Min temp.',
    'MORNING': 'Morning',
    'NIGHT': 'Night',
    'NOON': 'Noon',
    'PRESSURE': 'Pressure',
    'SUNRISE': 'Sunrise',
    'SUNSET': 'Sunset',
    'TEMPERATURE': 'Temperature',
    'UV INDEX': 'UV index',
    'VISIBILITY': 'Visibility',
    'WIND': 'Wind',
}


WEATHER_CONDITIONS = [
    # The capitalized string goes into to i18n/l10n (en: "Clear sky" -> de: "wolkenloser Himmel")
    msg.capitalize()
    for msg in typing.get_args(WeatherConditionType)
]

SOCIAL_MEDIA_TERMS = {
    'SUBSCRIBERS': 'subscribers',
    'POSTS': 'posts',
    'ACTIVE USERS': 'active users',
    'COMMENTS': 'comments',
    'USER': 'user',
    'COMMUNITY': 'community',
    'POINTS': 'points',
    'TITLE': 'title',
    'AUTHOR': 'author',
    'THREAD OPEN': 'open',
    'THREAD CLOSED': 'closed',
    'THREAD ANSWERED': 'answered',
}
