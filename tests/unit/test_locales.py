# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Test some code from module :py:obj:`searx.locales`"""

from searx import locales
from searx.sxng_locales import sxng_locales
from tests import SearxTestCase


class TestLocales(SearxTestCase):
    """Implemented tests:

    - :py:obj:`searx.locales.match_locale`
    """

    def test_match_locale(self):

        locale_tag_list = [x[0] for x in sxng_locales]

        # Test SearXNG search languages

        self.assertEqual(locales.match_locale('de', locale_tag_list), 'de')
        self.assertEqual(locales.match_locale('fr', locale_tag_list), 'fr')
        self.assertEqual(locales.match_locale('zh', locale_tag_list), 'zh')

        # Test SearXNG search regions

        self.assertEqual(locales.match_locale('ca-es', locale_tag_list), 'ca-ES')
        self.assertEqual(locales.match_locale('de-at', locale_tag_list), 'de-AT')
        self.assertEqual(locales.match_locale('de-de', locale_tag_list), 'de-DE')
        self.assertEqual(locales.match_locale('en-UK', locale_tag_list), 'en-GB')
        self.assertEqual(locales.match_locale('fr-be', locale_tag_list), 'fr-BE')
        self.assertEqual(locales.match_locale('fr-be', locale_tag_list), 'fr-BE')
        self.assertEqual(locales.match_locale('fr-ca', locale_tag_list), 'fr-CA')
        self.assertEqual(locales.match_locale('fr-ch', locale_tag_list), 'fr-CH')
        self.assertEqual(locales.match_locale('zh-cn', locale_tag_list), 'zh-CN')
        self.assertEqual(locales.match_locale('zh-tw', locale_tag_list), 'zh-TW')
        self.assertEqual(locales.match_locale('zh-hk', locale_tag_list), 'zh-HK')

        # Test language script code

        self.assertEqual(locales.match_locale('zh-hans', locale_tag_list), 'zh-CN')
        self.assertEqual(locales.match_locale('zh-hans-cn', locale_tag_list), 'zh-CN')
        self.assertEqual(locales.match_locale('zh-hant', locale_tag_list), 'zh-TW')
        self.assertEqual(locales.match_locale('zh-hant-tw', locale_tag_list), 'zh-TW')

        # Test individual locale lists

        self.assertEqual(locales.match_locale('es', [], fallback='fallback'), 'fallback')

        self.assertEqual(locales.match_locale('de', ['de-CH', 'de-DE']), 'de-DE')
        self.assertEqual(locales.match_locale('de', ['de-CH', 'de-DE']), 'de-DE')
        self.assertEqual(locales.match_locale('es', ['ES']), 'ES')
        self.assertEqual(locales.match_locale('es', ['es-AR', 'es-ES', 'es-MX']), 'es-ES')
        self.assertEqual(locales.match_locale('es-AR', ['es-AR', 'es-ES', 'es-MX']), 'es-AR')
        self.assertEqual(locales.match_locale('es-CO', ['es-AR', 'es-ES']), 'es-ES')
        self.assertEqual(locales.match_locale('es-CO', ['es-AR']), 'es-AR')

        # Tests from the commit message of 9ae409a05a

        # Assumption:
        #   A. When a user selects a language the results should be optimized according to
        #      the selected language.
        #
        #   B. When user selects a language and a territory the results should be
        #      optimized with first priority on territory and second on language.

        # Assume we have an engine that supports the follwoing locales:
        locale_tag_list = ['zh-CN', 'zh-HK', 'nl-BE', 'fr-CA']

        # Examples (Assumption A.)
        # ------------------------

        # A user selects region 'zh-TW' which should end in zh_HK.
        # hint: CN is 'Hans' and HK ('Hant') fits better to TW ('Hant')
        self.assertEqual(locales.match_locale('zh-TW', locale_tag_list), 'zh-HK')

        # A user selects only the language 'zh' which should end in CN
        self.assertEqual(locales.match_locale('zh', locale_tag_list), 'zh-CN')

        # A user selects only the language 'fr' which should end in fr_CA
        self.assertEqual(locales.match_locale('fr', locale_tag_list), 'fr-CA')

        # The difference in priority on the territory is best shown with a
        # engine that supports the following locales:
        locale_tag_list = ['fr-FR', 'fr-CA', 'en-GB', 'nl-BE']

        # A user selects only a language
        self.assertEqual(locales.match_locale('en', locale_tag_list), 'en-GB')

        # hint: the engine supports fr_FR and fr_CA since no territory is given,
        # fr_FR takes priority ..
        self.assertEqual(locales.match_locale('fr', locale_tag_list), 'fr-FR')

        # Examples (Assumption B.)
        # ------------------------

        #  A user selects region 'fr-BE' which should end in nl-BE
        self.assertEqual(locales.match_locale('fr-BE', locale_tag_list), 'nl-BE')

        # If the user selects a language and there are two locales like the
        # following:

        locale_tag_list = ['fr-BE', 'fr-CH']

        # The get_engine_locale selects the locale by looking at the "population
        # percent" and this percentage has an higher amount in BE (68.%)
        # compared to CH (21%)

        self.assertEqual(locales.match_locale('fr', locale_tag_list), 'fr-BE')
