# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import searx.plugins

from searx.engines import engines
from searx.preferences import Preferences
from searx.search.models import EngineRef
from searx.webadapter import validate_engineref_list

from tests import SearxTestCase

PRIVATE_ENGINE_NAME = "dummy private engine"  # from the ./settings/test_settings.yml
SEARCHQUERY = [EngineRef(PRIVATE_ENGINE_NAME, "general")]


class ValidateQueryCase(SearxTestCase):

    def test_without_token(self):
        preferences = Preferences(['simple'], ['general'], engines, searx.plugins.STORAGE)
        valid, unknown, invalid_token = validate_engineref_list(SEARCHQUERY, preferences)
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(unknown), 0)
        self.assertEqual(len(invalid_token), 1)

    def test_with_incorrect_token(self):
        preferences_with_tokens = Preferences(['simple'], ['general'], engines, searx.plugins.STORAGE)
        preferences_with_tokens.parse_dict({'tokens': 'bad-token'})
        valid, unknown, invalid_token = validate_engineref_list(SEARCHQUERY, preferences_with_tokens)
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(unknown), 0)
        self.assertEqual(len(invalid_token), 1)

    def test_with_correct_token(self):
        preferences_with_tokens = Preferences(['simple'], ['general'], engines, searx.plugins.STORAGE)
        preferences_with_tokens.parse_dict({'tokens': 'my-token'})
        valid, unknown, invalid_token = validate_engineref_list(SEARCHQUERY, preferences_with_tokens)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(unknown), 0)
        self.assertEqual(len(invalid_token), 0)
