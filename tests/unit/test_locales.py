# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

"""Test some code from module :py:obj:`searx.locales`"""

from parameterized import parameterized
from searx import locales
from searx.sxng_locales import sxng_locales
from tests import SearxTestCase


class TestLocales(SearxTestCase):
    """Implemented tests:

    - :py:obj:`searx.locales.match_locale`
    """

    @classmethod
    def setUpClass(cls):
        cls.locale_tag_list = [x[0] for x in sxng_locales]

    @parameterized.expand(
        [
            'de',
            'fr',
            'zh',
        ]
    )
    def test_locale_languages(self, locale: str):
        # Test SearXNG search languages
        self.assertEqual(locales.match_locale(locale, self.locale_tag_list), locale)

    @parameterized.expand(
        [
            ('de-at', 'de-AT'),
            ('de-de', 'de-DE'),
            ('en-UK', 'en-GB'),
            ('fr-be', 'fr-BE'),
            ('fr-ca', 'fr-CA'),
            ('fr-ch', 'fr-CH'),
            ('zh-cn', 'zh-CN'),
            ('zh-tw', 'zh-TW'),
            ('zh-hk', 'zh-HK'),
        ]
    )
    def test_match_region(self, locale: str, expected_locale: str):
        # Test SearXNG search regions
        self.assertEqual(locales.match_locale(locale, self.locale_tag_list), expected_locale)

    @parameterized.expand(
        [
            ('zh-hans', 'zh-CN'),
            ('zh-hans-cn', 'zh-CN'),
            ('zh-hant', 'zh-TW'),
            ('zh-hant-tw', 'zh-TW'),
        ]
    )
    def test_match_lang_script_code(self, locale: str, expected_locale: str):
        # Test language script code
        self.assertEqual(locales.match_locale(locale, self.locale_tag_list), expected_locale)

    def test_locale_de(self):
        self.assertEqual(locales.match_locale('de', ['de-CH', 'de-DE']), 'de-DE')
        self.assertEqual(locales.match_locale('de', ['de-CH', 'de-DE']), 'de-DE')

    def test_locale_es(self):
        self.assertEqual(locales.match_locale('es', [], fallback='fallback'), 'fallback')
        self.assertEqual(locales.match_locale('es', ['ES']), 'ES')
        self.assertEqual(locales.match_locale('es', ['es-AR', 'es-ES', 'es-MX']), 'es-ES')
        self.assertEqual(locales.match_locale('es-AR', ['es-AR', 'es-ES', 'es-MX']), 'es-AR')
        self.assertEqual(locales.match_locale('es-CO', ['es-AR', 'es-ES']), 'es-ES')
        self.assertEqual(locales.match_locale('es-CO', ['es-AR']), 'es-AR')

    @parameterized.expand(
        [
            ('zh-TW', ['zh-HK'], 'zh-HK'),  # A user selects region 'zh-TW' which should end in zh_HK.
            # hint: CN is 'Hans' and HK ('Hant') fits better to TW ('Hant')
            ('zh', ['zh-CN'], 'zh-CN'),  # A user selects only the language 'zh' which should end in CN
            ('fr', ['fr-CA'], 'fr-CA'),  # A user selects only the language 'fr' which should end in fr_CA
            ('nl', ['nl-BE'], 'nl-BE'),  # A user selects only the language 'fr' which should end in fr_CA
            # Territory tests
            ('en', ['en-GB'], 'en-GB'),  # A user selects only a language
            (
                'fr',
                ['fr-FR', 'fr-CA'],
                'fr-FR',
            ),  # the engine supports fr_FR and fr_CA since no territory is given, fr_FR takes priority
        ]
    )
    def test_locale_optimized_selected(self, locale: str, locale_list: list[str], expected_locale: str):
        """
        Tests from the commit message of 9ae409a05a

        Assumption:
          A. When a user selects a language the results should be optimized according to
             the selected language.
        """
        self.assertEqual(locales.match_locale(locale, locale_list), expected_locale)

    @parameterized.expand(
        [
            # approximation rule (*by territory*) -> territory has priority over the lang:
            # A user selects region 'fr-BE' which should end in nl-BE
            ('fr-BE', ['fr-FR', 'fr-CA', 'nl-BE'], 'nl-BE'),
            # approximation rule (*by language*) -> Check in which territories
            # the language has an official status and if one of these
            # territories is supported:
            # A user selects fr with 2 locales where fr is a offical language,
            # the get_engine_locale selects the locale by looking at the
            # "population percent" and this percentage has a higher amount in
            # BE (population 38%) compared to IT (population 20).
            ('fr', ['fr-BE', 'fr-IT'], 'fr-BE'),
        ]
    )
    def test_locale_optimized_territory(self, locale: str, locale_list: list[str], expected_locale: str):
        """
        Tests from the commit message of 9ae409a05a

          B. When user selects a language and a territory the results should be
             optimized with first priority on territory and second on language.
        """
        self.assertEqual(locales.match_locale(locale, locale_list), expected_locale)
