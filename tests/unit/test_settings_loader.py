# SPDX-License-Identifier: AGPL-3.0-or-later

from os.path import dirname, join, abspath
from unittest.mock import patch

from searx.exceptions import SearxSettingsException
from searx import settings_loader
from tests import SearxTestCase


test_dir = abspath(dirname(__file__))


class TestLoad(SearxTestCase):
    def test_load_zero(self):
        with self.assertRaises(SearxSettingsException):
            settings_loader.load_yaml('/dev/zero')

        with self.assertRaises(SearxSettingsException):
            settings_loader.load_yaml(join(test_dir, '/settings/syntaxerror_settings.yml'))

        with self.assertRaises(SearxSettingsException):
            settings_loader.load_yaml(join(test_dir, '/settings/empty_settings.yml'))

    def test_existing_filename_or_none(self):
        self.assertIsNone(settings_loader.existing_filename_or_none('/dev/zero'))

        bad_settings_path = join(test_dir, 'settings/syntaxerror_settings.yml')
        self.assertEqual(settings_loader.existing_filename_or_none(bad_settings_path), bad_settings_path)


class TestDefaultSettings(SearxTestCase):
    def test_load(self):
        settings, msg = settings_loader.load_settings(load_user_settings=False)
        self.assertTrue(msg.startswith('load the default settings from'))
        self.assertFalse(settings['general']['debug'])
        self.assertTrue(isinstance(settings['general']['instance_name'], str))
        self.assertEqual(settings['server']['secret_key'], "ultrasecretkey")
        self.assertTrue(isinstance(settings['server']['port'], int))
        self.assertTrue(isinstance(settings['server']['bind_address'], str))
        self.assertTrue(isinstance(settings['engines'], list))
        self.assertTrue(isinstance(settings['doi_resolvers'], dict))
        self.assertTrue(isinstance(settings['default_doi_resolver'], str))


class TestUserSettings(SearxTestCase):
    def test_is_use_default_settings(self):
        self.assertFalse(settings_loader.is_use_default_settings({}))
        self.assertTrue(settings_loader.is_use_default_settings({'use_default_settings': True}))
        self.assertTrue(settings_loader.is_use_default_settings({'use_default_settings': {}}))
        with self.assertRaises(ValueError):
            self.assertFalse(settings_loader.is_use_default_settings({'use_default_settings': 1}))
        with self.assertRaises(ValueError):
            self.assertFalse(settings_loader.is_use_default_settings({'use_default_settings': 0}))

    def test_user_settings_not_found(self):
        with patch.dict(settings_loader.environ, {'SEARXNG_SETTINGS_PATH': '/dev/null'}):
            settings, msg = settings_loader.load_settings()
            self.assertTrue(msg.startswith('load the default settings from'))
            self.assertEqual(settings['server']['secret_key'], "ultrasecretkey")

    def test_user_settings(self):
        with patch.dict(
            settings_loader.environ, {'SEARXNG_SETTINGS_PATH': join(test_dir, 'settings/user_settings_simple.yml')}
        ):
            settings, msg = settings_loader.load_settings()
            self.assertTrue(msg.startswith('merge the default settings'))
            self.assertEqual(settings['server']['secret_key'], "user_secret_key")
            self.assertEqual(settings['server']['default_http_headers']['Custom-Header'], "Custom-Value")

    def test_user_settings_remove(self):
        with patch.dict(
            settings_loader.environ, {'SEARXNG_SETTINGS_PATH': join(test_dir, 'settings/user_settings_remove.yml')}
        ):
            settings, msg = settings_loader.load_settings()
            self.assertTrue(msg.startswith('merge the default settings'))
            self.assertEqual(settings['server']['secret_key'], "user_secret_key")
            self.assertEqual(settings['server']['default_http_headers']['Custom-Header'], "Custom-Value")
            engine_names = [engine['name'] for engine in settings['engines']]
            self.assertNotIn('wikinews', engine_names)
            self.assertNotIn('wikibooks', engine_names)
            self.assertIn('wikipedia', engine_names)

    def test_user_settings_remove2(self):
        with patch.dict(
            settings_loader.environ, {'SEARXNG_SETTINGS_PATH': join(test_dir, 'settings/user_settings_remove2.yml')}
        ):
            settings, msg = settings_loader.load_settings()
            self.assertTrue(msg.startswith('merge the default settings'))
            self.assertEqual(settings['server']['secret_key'], "user_secret_key")
            self.assertEqual(settings['server']['default_http_headers']['Custom-Header'], "Custom-Value")
            engine_names = [engine['name'] for engine in settings['engines']]
            self.assertNotIn('wikinews', engine_names)
            self.assertNotIn('wikibooks', engine_names)
            self.assertIn('wikipedia', engine_names)
            wikipedia = list(filter(lambda engine: (engine.get('name')) == 'wikipedia', settings['engines']))
            self.assertEqual(wikipedia[0]['engine'], 'wikipedia')
            self.assertEqual(wikipedia[0]['tokens'], ['secret_token'])
            newengine = list(filter(lambda engine: (engine.get('name')) == 'newengine', settings['engines']))
            self.assertEqual(newengine[0]['engine'], 'dummy')

    def test_user_settings_keep_only(self):
        with patch.dict(
            settings_loader.environ, {'SEARXNG_SETTINGS_PATH': join(test_dir, 'settings/user_settings_keep_only.yml')}
        ):
            settings, msg = settings_loader.load_settings()
            self.assertTrue(msg.startswith('merge the default settings'))
            engine_names = [engine['name'] for engine in settings['engines']]
            self.assertEqual(engine_names, ['wikibooks', 'wikinews', 'wikipedia', 'newengine'])
            # wikipedia has been removed, then added again with the "engine" section of user_settings_keep_only.yml
            self.assertEqual(len(settings['engines'][2]), 1)

    def test_custom_settings(self):
        with patch.dict(
            settings_loader.environ, {'SEARXNG_SETTINGS_PATH': join(test_dir, 'settings/user_settings.yml')}
        ):
            settings, msg = settings_loader.load_settings()
            self.assertTrue(msg.startswith('load the user settings from'))
            self.assertEqual(settings['server']['port'], 9000)
            self.assertEqual(settings['server']['secret_key'], "user_settings_secret")
            engine_names = [engine['name'] for engine in settings['engines']]
            self.assertEqual(engine_names, ['wikidata', 'wikibooks', 'wikinews', 'wikiquote'])
