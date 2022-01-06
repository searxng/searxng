from searx.preferences import (
    EnumStringSetting,
    MapSetting,
    SearchLanguageSetting,
    MultipleChoiceSetting,
    PluginsSetting,
    ValidationException,
)
from tests import SearxTestCase


class PluginStub:
    def __init__(self, plugin_id, default_on):
        self.id = plugin_id
        self.default_on = default_on


class TestSettings(SearxTestCase):
    # map settings

    def test_map_setting_invalid_default_value(self):
        with self.assertRaises(ValidationException):
            MapSetting(3, map={'dog': 1, 'bat': 2})

    def test_map_setting_invalid_choice(self):
        setting = MapSetting(2, map={'dog': 1, 'bat': 2})
        with self.assertRaises(ValidationException):
            setting.parse('cat')

    def test_map_setting_valid_default(self):
        setting = MapSetting(3, map={'dog': 1, 'bat': 2, 'cat': 3})
        self.assertEqual(setting.get_value(), 3)

    def test_map_setting_valid_choice(self):
        setting = MapSetting(3, map={'dog': 1, 'bat': 2, 'cat': 3})
        self.assertEqual(setting.get_value(), 3)
        setting.parse('bat')
        self.assertEqual(setting.get_value(), 2)

    # enum settings

    def test_enum_setting_invalid_default_value(self):
        with self.assertRaises(ValidationException):
            EnumStringSetting(3, choices=[0, 1, 2])

    def test_enum_setting_invalid_choice(self):
        setting = EnumStringSetting(0, choices=[0, 1, 2])
        with self.assertRaises(ValidationException):
            setting.parse(3)

    def test_enum_setting_valid_default(self):
        setting = EnumStringSetting(3, choices=[1, 2, 3])
        self.assertEqual(setting.get_value(), 3)

    def test_enum_setting_valid_choice(self):
        setting = EnumStringSetting(3, choices=[1, 2, 3])
        self.assertEqual(setting.get_value(), 3)
        setting.parse(2)
        self.assertEqual(setting.get_value(), 2)

    # multiple choice settings

    def test_multiple_setting_invalid_default_value(self):
        with self.assertRaises(ValidationException):
            MultipleChoiceSetting(['3', '4'], choices=['0', '1', '2'])

    def test_multiple_setting_invalid_choice(self):
        setting = MultipleChoiceSetting(['1', '2'], choices=['0', '1', '2'])
        with self.assertRaises(ValidationException):
            setting.parse('4, 3')

    def test_multiple_setting_valid_default(self):
        setting = MultipleChoiceSetting(['3'], choices=['1', '2', '3'])
        self.assertEqual(setting.get_value(), ['3'])

    def test_multiple_setting_valid_choice(self):
        setting = MultipleChoiceSetting(['3'], choices=['1', '2', '3'])
        self.assertEqual(setting.get_value(), ['3'])
        setting.parse('2')
        self.assertEqual(setting.get_value(), ['2'])

    # search language settings
    def test_lang_setting_valid_choice(self):
        setting = SearchLanguageSetting('all', choices=['all', 'de', 'en'])
        setting.parse('de')
        self.assertEqual(setting.get_value(), 'de')

    def test_lang_setting_invalid_choice(self):
        setting = SearchLanguageSetting('all', choices=['all', 'de', 'en'])
        setting.parse('xx')
        self.assertEqual(setting.get_value(), 'all')

    def test_lang_setting_old_cookie_choice(self):
        setting = SearchLanguageSetting('all', choices=['all', 'es', 'es-ES'])
        setting.parse('es_XA')
        self.assertEqual(setting.get_value(), 'es')

    def test_lang_setting_old_cookie_format(self):
        setting = SearchLanguageSetting('all', choices=['all', 'es', 'es-ES'])
        setting.parse('es_ES')
        self.assertEqual(setting.get_value(), 'es-ES')

    # plugins settings
    def test_plugins_setting_all_default_enabled(self):
        plugin1 = PluginStub('plugin1', True)
        plugin2 = PluginStub('plugin2', True)
        setting = PluginsSetting(['3'], plugins=[plugin1, plugin2])
        self.assertEqual(set(setting.get_enabled()), set(['plugin1', 'plugin2']))

    def test_plugins_setting_few_default_enabled(self):
        plugin1 = PluginStub('plugin1', True)
        plugin2 = PluginStub('plugin2', False)
        plugin3 = PluginStub('plugin3', True)
        setting = PluginsSetting('name', plugins=[plugin1, plugin2, plugin3])
        self.assertEqual(set(setting.get_enabled()), set(['plugin1', 'plugin3']))


class TestPreferences(SearxTestCase):
    def test_encode(self):
        from searx.preferences import Preferences

        pref = Preferences(['oscar'], ['general'], {}, [])
        url_params = (
            'eJx1VMmO2zAM_Zr6YrTocujJh6JF0QEKzKAz7VVgJNohLIseUU7ivy-VcWy5yyGOTVGP73GLKJNPYjiYgGeT4NB8BS9YOSY'
            'TUdifMDYM-vmGY1d5CN0EHTYOK88W_PXNkcDBozOjnzoK0vyi4bWnHs2RU4-zvHr_-RF9a-5Cy3GARByy7X7EkKMoBeMp9CuPQ-SzYMx'
            '8Vr9P1qKI-XJ_p1fOkRJWNCgVM0a-zAttmBJbHkaPSZlNts-_jiuBFgUh2mPztkpHHLBhsRArDHvm356eHh5vATS0Mqagr0ZsZO_V8hT'
            'B9srt54_v6jewJugqL4Nn_hYSdhxnI-jRpi05GDQCStOT7UGVmJY8ZnltRKyF23SGiLWjqNcygKGkpyeGZIywJfD1gI5AjRTAmBM55Aw'
            'Q0Tn626lj7jzWo4e5hnEsIlprX6dTgdBRpyRBFKTDgBF8AasVyT4gvSTEoXRpXWRyG3CYQYld65I_V6lboILTMAlZY65_ejRDcHgp0Tv'
            'EPtGAsqTiBf3m76g7pP9B84mwjPvuUtASRDei1nDF2ix_JXW91UJkXrPh6RAhznVmKyQl7dwJdMJ6bz1QOmgzYlrEzHDMcEUuo44AgS1'
            'CvkjaOb2Q2AyY5oGDTs_OLXE_c2I5cg9hk3kEJZ0fu4SuktsIA2RhuJwP86AdripThCBeO9uVUejyPGmFSxPrqEYcuWi25zOEXV9tc1m'
            '_KP1nafYtdfv6Q9hKfWmGm9A_3G635UwiVndLGdFCiLWkONk0xUxGLGGweGWTa2nZYZ0fS1YKlE3Uuw8fPl52E5U8HJYbC7sbjXUsrnT'
            'XHXRbELfO-1fGSqskiGnMK7B0dV3t8Lq08pbdtYpuVdoKWA2Yjuyah_vHp2rZWjo0zXL8Gw8DTj0='
        )
        pref.parse_encoded_data(url_params)
        self.assertEqual(
            vars(pref.key_value_settings['categories']),
            {'value': ['general'], 'locked': False, 'choices': ['general', 'none']},
        )
