# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import babel
from mock import Mock

import searx
import searx.plugins
import searx.preferences
import searx.results

from searx.result_types import Result
from searx.extended_types import sxng_request

from tests import SearxTestCase

plg_store = searx.plugins.PluginStorage()
plg_store.load_settings(searx.get_setting("plugins"))


def get_search_mock(query, **kwargs):

    lang = kwargs.get("lang", "en-US")
    kwargs["pageno"] = kwargs.get("pageno", 1)
    kwargs["locale"] = babel.Locale.parse(lang, sep="-")
    user_plugins = kwargs.pop("user_plugins", [x.id for x in plg_store])

    return Mock(
        search_query=Mock(query=query, **kwargs),
        user_plugins=user_plugins,
        result_container=searx.results.ResultContainer(),
    )


def do_pre_search(query, storage, **kwargs) -> bool:

    search = get_search_mock(query, **kwargs)
    ret = storage.pre_search(sxng_request, search)
    return ret


def do_post_search(query, storage, **kwargs) -> Mock:

    search = get_search_mock(query, **kwargs)
    storage.post_search(sxng_request, search)
    return search


class PluginMock(searx.plugins.Plugin):

    def __init__(self, _id: str, name: str, active: bool):
        plg_cfg = searx.plugins.PluginCfg(active=active)
        self.id = _id
        self._name = name
        super().__init__(plg_cfg)

    # pylint: disable= unused-argument
    def pre_search(self, request, search) -> bool:
        return True

    def post_search(self, request, search) -> None:
        return None

    def on_result(self, request, search, result) -> bool:
        return False

    def info(self):
        return searx.plugins.PluginInfo(
            id=self.id,
            name=self._name,
            description=f"Dummy plugin: {self.id}",
            preference_section="general",
        )


class PluginStorage(SearxTestCase):

    def setUp(self):
        super().setUp()
        engines = {}

        self.storage = searx.plugins.PluginStorage()
        self.storage.register(PluginMock("plg001", "first plugin", True))
        self.storage.register(PluginMock("plg002", "second plugin", True))
        self.storage.init(self.app)
        self.pref = searx.preferences.Preferences(["simple"], ["general"], engines, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def test_init(self):

        self.assertEqual(2, len(self.storage))

    def test_hooks(self):

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            query = ""

            ret = do_pre_search(query, self.storage, pageno=1)
            self.assertTrue(ret is True)

            ret = self.storage.on_result(
                sxng_request,
                get_search_mock("lorem ipsum", user_plugins=["plg001", "plg002"]),
                Result(),
            )
            self.assertFalse(ret)
