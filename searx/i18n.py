# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pylint: disable=missing-module-docstring,missing-function-docstring

import babel
import babel.numbers
import babel.dates
import babel.support

from starlette_i18n import (
    i18n,
    load_gettext_translations,
)
from starlette_i18n import gettext_lazy as gettext

__all__ = (
    'gettext',
    'format_decimal',
    'format_date',
    'initialize_i18n'
)


def format_decimal(number, format=None):  # pylint: disable=redefined-builtin
    locale = i18n.get_locale()
    return babel.numbers.format_decimal(number, format=format, locale=locale)


def format_date(date=None, format='medium', rebase=False):  # pylint: disable=redefined-builtin
    if rebase:
        raise ValueError('rebase=True not implemented')
    locale = i18n.get_locale()
    if format in ('full', 'long', 'medium', 'short'):
        format = locale.date_formats[format]
    pattern = babel.dates.parse_pattern(format)
    return pattern.apply(date, locale)


def monkeypatch():
    old_i18n_Locale_parse = i18n.Locale.parse
    def i18n_Locale_parse(identifier, sep='_', resolve_likely_subtags=True):
        if identifier == 'oc':
            identifier = 'fr'
        return old_i18n_Locale_parse(identifier, sep, resolve_likely_subtags)
    setattr(i18n.Locale, 'parse', i18n_Locale_parse)


def initialize_i18n(translations_path):
    monkeypatch()
    load_gettext_translations(directory=translations_path, domain="messages")
