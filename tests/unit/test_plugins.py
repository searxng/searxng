# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import babel
from mock import Mock
from searx import plugins
from tests import SearxTestCase


def get_search_mock(query, **kwargs):
    lang = kwargs.get("lang", "en-US")
    kwargs["locale"] = babel.Locale.parse(lang, sep="-")
    return Mock(search_query=Mock(query=query, **kwargs), result_container=Mock(answers={}))


class PluginMock:  # pylint: disable=missing-class-docstring, too-few-public-methods
    default_on = False
    name = 'Default plugin'
    description = 'Default plugin description'


class PluginStoreTest(SearxTestCase):  # pylint: disable=missing-class-docstring
    def setUp(self):
        self.store = plugins.PluginStore()

    def test_init(self):
        self.assertEqual(0, len(self.store.plugins))
        self.assertIsInstance(self.store.plugins, list)

    def test_register(self):
        testplugin = PluginMock()
        self.store.register(testplugin)
        self.assertEqual(1, len(self.store.plugins))

    def test_call_empty(self):
        testplugin = PluginMock()
        self.store.register(testplugin)
        setattr(testplugin, 'asdf', Mock())
        request = Mock()
        self.store.call([], 'asdf', request, Mock())
        self.assertFalse(getattr(testplugin, 'asdf').called)  # pylint: disable=E1101

    def test_call_with_plugin(self):
        store = plugins.PluginStore()
        testplugin = PluginMock()
        store.register(testplugin)
        setattr(testplugin, 'asdf', Mock())
        request = Mock()
        store.call([testplugin], 'asdf', request, Mock())
        self.assertTrue(getattr(testplugin, 'asdf').called)  # pylint: disable=E1101
