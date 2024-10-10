# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, invalid-name

from mock import Mock
from parameterized.parameterized import parameterized

from searx import (
    plugins,
    limiter,
    botdetection,
)
from tests import SearxTestCase
from .test_plugins import get_search_mock


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
