# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from mock import Mock
from parameterized.parameterized import parameterized

from searx import (
    plugins,
    limiter,
    botdetection,
)

from tests import SearxTestCase


def get_search_mock(query, **kwargs):
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


class PluginIPSelfInfo(SearxTestCase):  # pylint: disable=missing-class-docstring
    def setUp(self):
        plugin = plugins.load_and_initialize_plugin('searx.plugins.self_info', False, (None, {}))
        self.store = plugins.PluginStore()
        self.store.register(plugin)
        cfg = limiter.get_cfg()
        botdetection.init(cfg, None)

    def test_plugin_store_init(self):
        self.assertEqual(1, len(self.store.plugins))

    def test_ip_in_answer(self):
        request = Mock()
        request.remote_addr = '127.0.0.1'
        request.headers = {'X-Forwarded-For': '1.2.3.4, 127.0.0.1', 'X-Real-IP': '127.0.0.1'}
        search = get_search_mock(query='ip', pageno=1)
        self.store.call(self.store.plugins, 'post_search', request, search)
        self.assertIn('127.0.0.1', search.result_container.answers["ip"]["answer"])

    def test_ip_not_in_answer(self):
        request = Mock()
        request.remote_addr = '127.0.0.1'
        request.headers = {'X-Forwarded-For': '1.2.3.4, 127.0.0.1', 'X-Real-IP': '127.0.0.1'}
        search = get_search_mock(query='ip', pageno=2)
        self.store.call(self.store.plugins, 'post_search', request, search)
        self.assertNotIn('ip', search.result_container.answers)

    @parameterized.expand(
        [
            'user-agent',
            'What is my User-Agent?',
        ]
    )
    def test_user_agent_in_answer(self, query: str):
        request = Mock(user_agent=Mock(string='Mock'))
        search = get_search_mock(query=query, pageno=1)
        self.store.call(self.store.plugins, 'post_search', request, search)
        self.assertIn('Mock', search.result_container.answers["user-agent"]["answer"])

    @parameterized.expand(
        [
            'user-agent',
            'What is my User-Agent?',
        ]
    )
    def test_user_agent_not_in_answer(self, query: str):
        request = Mock(user_agent=Mock(string='Mock'))
        search = get_search_mock(query=query, pageno=2)
        self.store.call(self.store.plugins, 'post_search', request, search)
        self.assertNotIn('user-agent', search.result_container.answers)


class PluginHashTest(SearxTestCase):  # pylint: disable=missing-class-docstring
    def setUp(self):
        self.store = plugins.PluginStore()
        plugin = plugins.load_and_initialize_plugin('searx.plugins.hash_plugin', False, (None, {}))
        self.store.register(plugin)

    def test_plugin_store_init(self):
        self.assertEqual(1, len(self.store.plugins))

    @parameterized.expand(
        [
            ('md5 test', 'md5 hash digest: 098f6bcd4621d373cade4e832627b4f6'),
            ('sha1 test', 'sha1 hash digest: a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'),
            ('sha224 test', 'sha224 hash digest: 90a3ed9e32b2aaf4c61c410eb925426119e1a9dc53d4286ade99a809'),
            ('sha256 test', 'sha256 hash digest: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'),
            (
                'sha384 test',
                'sha384 hash digest: 768412320f7b0aa5812fce428dc4706b3c'
                'ae50e02a64caa16a782249bfe8efc4b7ef1ccb126255d196047dfedf1'
                '7a0a9',
            ),
            (
                'sha512 test',
                'sha512 hash digest: ee26b0dd4af7e749aa1a8ee3c10ae9923f6'
                '18980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5'
                'fa9ad8e6f57f50028a8ff',
            ),
        ]
    )
    def test_hash_digest_new(self, query: str, hash_str: str):
        request = Mock(remote_addr='127.0.0.1')
        search = get_search_mock(query=query, pageno=1)
        self.store.call(self.store.plugins, 'post_search', request, search)
        self.assertIn(hash_str, search.result_container.answers['hash']['answer'])

    def test_md5_bytes_no_answer(self):
        request = Mock(remote_addr='127.0.0.1')
        search = get_search_mock(query=b'md5 test', pageno=2)
        self.store.call(self.store.plugins, 'post_search', request, search)
        self.assertNotIn('hash', search.result_container.answers)
