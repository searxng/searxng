# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name,protected-access
# pylint: disable=too-many-public-methods

import json
from base64 import urlsafe_b64decode
from contextlib import contextmanager
from zlib import decompress

from mock import Mock

import searx.ai_summary
import searx.plugins
import searx.plugins.ai_summary
import searx.preferences

from searx.extended_types import sxng_request
from searx.result_types import AiSummary

from tests import SearxTestCase
from .test_plugins import get_search_mock

PLUGIN_FQN = "searx.plugins.ai_summary.SXNGPlugin"
BASE_URL = "http://127.0.0.1:11434"
MODEL = "test-model"


def sse_stream_mock(lines: list[dict], status_code: int = 200) -> Mock:
    """A mock httpx client whose ``stream()`` context manager yields the given
    objects as a SSE stream (OpenAI chat completions format)."""

    upstream = Mock(status_code=status_code)
    upstream.iter_lines.return_value = iter([f"data: {json.dumps(line)}" for line in lines] + ["data: [DONE]"])
    # httpx exposes the body of an error response as a str; the endpoint logs it
    upstream.text = ""

    @contextmanager
    def stream(*_args, **_kwargs):
        yield upstream

    client = Mock()
    client.stream = stream
    return client


class AISummaryAPIKey(SearxTestCase):
    """The API key is administrator configuration and must only be sent to the
    administrator's server, never to a server a user configured."""

    def setUp(self):
        super().setUp()
        self.cfg = searx.get_setting("ai_summary")
        self.setattr4test(self.cfg, "base_url", BASE_URL)
        self.setattr4test(self.cfg, "api_key", "sk-secret")

    def test_auth_header_set_for_api_key(self):
        with searx.plugins.ai_summary._get_client(BASE_URL, self.cfg, "sk-secret") as client:
            self.assertEqual(client.headers["Authorization"], "Bearer sk-secret")

    def test_no_auth_header_without_api_key(self):
        with searx.plugins.ai_summary._get_client(BASE_URL, self.cfg) as client:
            self.assertNotIn("Authorization", client.headers)

    def test_key_sent_to_admin_server(self):
        for server in [BASE_URL, BASE_URL + "/", BASE_URL + "/v1", "http://127.0.0.1:11434/v1/"]:
            self.assertEqual("sk-secret", searx.plugins.ai_summary._server_api_key(self.cfg, server), server)

    def test_key_not_sent_to_other_server(self):
        for server in [
            "http://192.168.1.10:11434",  # other host
            "http://127.0.0.1:8080",  # other port
            "https://127.0.0.1:11434",  # other scheme
            "http://127.0.0.1:11434/other",  # other path
            # the userinfo of a URL must not be mistaken for the host the
            # request is sent to
            "http://127.0.0.1:11434@untrusted.example.org",
            "not a url",
            "",
        ]:
            self.assertEqual("", searx.plugins.ai_summary._server_api_key(self.cfg, server), server)

    def test_no_key_configured(self):
        self.setattr4test(self.cfg, "api_key", "")
        self.assertEqual("", searx.plugins.ai_summary._server_api_key(self.cfg, BASE_URL))

    def test_user_key_goes_to_the_users_own_server(self):
        key = searx.plugins.ai_summary._server_api_key(self.cfg, "http://192.168.1.10:11434", "sk-users-own")
        self.assertEqual("sk-users-own", key)

    def test_user_key_does_not_override_the_admin_key(self):
        # the user's key belongs to the user's server; on the admin's server
        # the admin's key is the right one
        key = searx.plugins.ai_summary._server_api_key(self.cfg, BASE_URL, "sk-users-own")
        self.assertEqual("sk-secret", key)

    def test_no_key_for_a_user_server_without_a_user_key(self):
        self.assertEqual("", searx.plugins.ai_summary._server_api_key(self.cfg, "http://192.168.1.10:11434", ""))


class PluginAISummaryInit(SearxTestCase):

    def test_active_without_base_url(self):
        # the Ollama server can be configured by the user in the preferences,
        # the plugin stays active without an admin configured default
        self.setattr4test(searx.ai_summary, "MODELS", [])

        storage = searx.plugins.PluginStorage()
        storage.load_settings({PLUGIN_FQN: {"active": True}})
        storage.init(self.app)

        self.assertEqual(1, len(storage))
        self.assertEqual([], searx.ai_summary.MODELS)

    def test_model_list_from_settings(self):
        cfg = searx.get_setting("ai_summary")
        self.setattr4test(cfg, "base_url", BASE_URL)
        self.setattr4test(cfg, "model", MODEL)
        self.setattr4test(cfg, "models", [MODEL, "other-model"])
        self.setattr4test(searx.ai_summary, "MODELS", [])

        storage = searx.plugins.PluginStorage()
        storage.load_settings({PLUGIN_FQN: {"active": True}})
        storage.init(self.app)

        self.assertEqual(1, len(storage))
        self.assertEqual([MODEL, "other-model"], searx.ai_summary.MODELS)

    def test_model_probe_sends_api_key(self):
        cfg = searx.get_setting("ai_summary")
        self.setattr4test(cfg, "base_url", BASE_URL)
        self.setattr4test(cfg, "model", "")
        self.setattr4test(cfg, "models", [])
        self.setattr4test(cfg, "api_key", "sk-secret")
        self.setattr4test(searx.ai_summary, "MODELS", [])

        calls: list[tuple[str, str]] = []

        class _FakeClient:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def get(self, _path):
                resp = Mock()
                resp.json.return_value = {"data": [{"id": "probed-model"}]}
                return resp

        def record(base_url, _cfg, api_key=""):
            calls.append((base_url, api_key))
            return _FakeClient()

        self.setattr4test(searx.plugins.ai_summary, "_get_client", record)

        storage = searx.plugins.PluginStorage()
        storage.load_settings({PLUGIN_FQN: {"active": True}})
        storage.init(self.app)

        self.assertEqual([(BASE_URL, "sk-secret")], calls)
        self.assertEqual(["probed-model"], searx.ai_summary.MODELS)


class PluginAISummary(SearxTestCase):

    def setUp(self):
        super().setUp()

        cfg = searx.get_setting("ai_summary")
        self.setattr4test(cfg, "base_url", BASE_URL)
        self.setattr4test(cfg, "model", MODEL)
        self.setattr4test(cfg, "models", [MODEL])
        self.setattr4test(searx.ai_summary, "MODELS", [])

        self.storage = searx.plugins.PluginStorage()
        self.storage.load_settings({PLUGIN_FQN: {"active": True}})
        self.storage.init(self.app)

        # the endpoint checks request.user_plugins (built in webapp.pre_request
        # from the global plugin storage) -- enable the plugin like a browser
        # with saved preferences does
        self.client.set_cookie("disabled_plugins", "")
        self.client.set_cookie("enabled_plugins", "ai_summary")

        self.pref = searx.preferences.Preferences(["simple"], ["general"], {}, self.storage)
        self.pref.parse_dict({"locale": "en"})

    def mock_upstream(self, client_mock: Mock):
        self.setattr4test(searx.plugins.ai_summary, "_get_client", lambda *_args, **_kwargs: client_mock)

    def mock_upstream_recording(self, client_mock: Mock) -> list[tuple[str, str]]:
        """Like :py:obj:`mock_upstream`, the returned list records the
        ``(base_url, api_key)`` the endpoint requested a client for."""
        calls: list[tuple[str, str]] = []

        def record(base_url, _cfg, api_key=""):
            calls.append((base_url, api_key))
            return client_mock

        self.setattr4test(searx.plugins.ai_summary, "_get_client", record)
        return calls

    def do_post_search(self, query, **kwargs) -> Mock:
        kwargs.setdefault("categories", ["general"])
        search = get_search_mock(query, user_plugins=["ai_summary"], **kwargs)
        self.storage.post_search(sxng_request, search)
        return search

    def test_placeholder_answer_is_added(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref

            search = self.do_post_search("what is the best searx fork")
            answer = AiSummary(query="what is the best searx fork", grounding=False)
            self.assertIn(answer, search.result_container.answers)

    def test_placeholder_carries_grounding_pref(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            self.pref.parse_dict({"ai_summary_grounding": "1"})

            search = self.do_post_search("lorem ipsum")
            answer = list(search.result_container.answers)[0]
            self.assertTrue(answer.grounding)

    def test_grounding_is_on_by_default(self):
        # note: AiSummary.__hash__ is hash(query), so two answers that differ
        # only in .grounding compare equal -- assert on the attribute
        self.assertTrue(searx.get_setting("ai_summary").grounding)
        pref = searx.preferences.Preferences(["simple"], ["general"], {}, self.storage)

        with self.app.test_request_context():
            sxng_request.preferences = pref
            search = self.do_post_search("lorem ipsum")
            answer = list(search.result_container.answers)[0]
            self.assertTrue(answer.grounding)

    def test_grounding_can_be_disabled_by_settings(self):
        self.setattr4test(searx.get_setting("ai_summary"), "grounding", False)
        pref = searx.preferences.Preferences(["simple"], ["general"], {}, self.storage)

        with self.app.test_request_context():
            sxng_request.preferences = pref
            search = self.do_post_search("lorem ipsum")
            answer = list(search.result_container.answers)[0]
            self.assertFalse(answer.grounding)

    def test_skip_pageno(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            search = self.do_post_search("lorem ipsum", pageno=2)
            self.assertEqual(list(search.result_container.answers), [])

    def test_skip_non_html_format(self):
        with self.app.test_request_context("/search", method="POST", data={"format": "json"}):
            sxng_request.preferences = self.pref
            search = self.do_post_search("lorem ipsum")
            self.assertEqual(list(search.result_container.answers), [])

    def test_skip_non_general_category(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            search = self.do_post_search("lorem ipsum", categories=["images"])
            self.assertEqual(list(search.result_container.answers), [])

    def test_skip_infobox(self):
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            search = get_search_mock("lorem ipsum", user_plugins=["ai_summary"], categories=["general"])
            search.result_container.infoboxes.append(Mock())
            self.storage.post_search(sxng_request, search)
            self.assertEqual(list(search.result_container.answers), [])

    def test_skip_instant_answer(self):
        # e.g. the "ddg definitions" engine adds wikipedia abstracts as Answer
        from searx.result_types import Answer  # pylint: disable=import-outside-toplevel

        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            search = get_search_mock("lorem ipsum", user_plugins=["ai_summary"], categories=["general"])
            engine_answer = Answer(answer="Lorem ipsum is placeholder text.  More at Wikipedia")
            search.result_container.answers.add(engine_answer)
            self.storage.post_search(sxng_request, search)
            self.assertEqual(list(search.result_container.answers), [engine_answer])

    def test_skip_without_any_server(self):
        self.setattr4test(searx.get_setting("ai_summary"), "base_url", "")
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            search = self.do_post_search("lorem ipsum")
            self.assertEqual(list(search.result_container.answers), [])

    def test_placeholder_with_user_server_only(self):
        self.setattr4test(searx.get_setting("ai_summary"), "base_url", "")
        with self.app.test_request_context():
            sxng_request.preferences = self.pref
            self.pref.parse_dict({"ai_summary_server": "http://192.168.1.10:11434"})
            search = self.do_post_search("lorem ipsum")
            self.assertEqual(len(list(search.result_container.answers)), 1)

    def test_endpoint_forbidden_when_disabled(self):
        self.client.set_cookie("disabled_plugins", "ai_summary")
        self.client.set_cookie("enabled_plugins", "")
        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 403)

    def test_endpoint_bad_request(self):
        for body in [
            None,
            {},
            {"messages": []},
            {"messages": [{"role": "system", "content": "hi"}]},
            {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "ho"}]},
            {"messages": [{"role": "user", "content": "x" * 5000}]},
            {"messages": [{"role": "user", "content": "hi"}], "context": [{"unknown_key": "x"}]},
            {"messages": [{"role": "user", "content": "hi"}] * 13},
        ]:
            res = self.client.post("/ai_summary", json=body)
            self.assertEqual(res.status_code, 400, body)

    def test_endpoint_invalid_server_pref(self):
        self.client.set_cookie("ai_summary_server", "ftp://example.org")
        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 400)

    def test_endpoint_invalid_model_pref(self):
        # an empty preference is not invalid -- it falls back to the
        # administrator's default, which is covered by the tests above
        for model in ["bad model name!", "model;rm -rf", 'model"quoted', "model\nname", "x" * 129]:
            self.client.set_cookie("ai_summary_model", model)
            res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
            self.assertEqual(res.status_code, 400, model)

    def test_endpoint_accepts_provider_model_names(self):
        # model names differ per provider: a version pin (@), a gateway's
        # routing prefix (/) and an Ollama tag (:) are all valid names
        for model in [
            "gemma3:4b",
            "llama3.2:3b",
            "gemini-1.5-pro@001",
            "bedrock/anthropic.claude-3-5-sonnet",
            "azure/my-deployment",
        ]:
            self.mock_upstream(sse_stream_mock([]))
            self.client.set_cookie("ai_summary_model", model)
            res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
            self.assertEqual(res.status_code, 200, model)
            lines = [json.loads(line) for line in res.data.decode().splitlines() if line]
            self.assertEqual(lines[-1], {"done": True, "model": model})

    def test_endpoint_no_server_configured(self):
        self.setattr4test(searx.get_setting("ai_summary"), "base_url", "")
        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 400)

    def test_endpoint_streams_ndjson(self):
        self.mock_upstream(
            sse_stream_mock(
                [
                    {"choices": [{"delta": {"content": "Hello "}}]},
                    {"choices": [{"delta": {"content": "world"}}]},
                    {"choices": [{"delta": {}, "finish_reason": "stop"}]},
                ]
            )
        )

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/x-ndjson")

        lines = [json.loads(line) for line in res.data.decode().splitlines() if line]
        self.assertEqual(lines[0], {"delta": "Hello "})
        self.assertEqual(lines[1], {"delta": "world"})
        self.assertEqual(lines[2], {"done": True, "model": MODEL})

    def test_endpoint_model_pref_wins(self):
        self.mock_upstream(sse_stream_mock([]))
        self.client.set_cookie("ai_summary_model", "my-own-model:7b")

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        lines = [json.loads(line) for line in res.data.decode().splitlines() if line]
        self.assertEqual(lines[-1], {"done": True, "model": "my-own-model:7b"})

    def test_endpoint_sends_api_key_to_admin_server(self):
        self.setattr4test(searx.get_setting("ai_summary"), "api_key", "sk-secret")
        calls = self.mock_upstream_recording(sse_stream_mock([]))

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([(BASE_URL, "sk-secret")], calls)

    def test_endpoint_hides_api_key_from_user_server(self):
        self.setattr4test(searx.get_setting("ai_summary"), "api_key", "sk-secret")
        calls = self.mock_upstream_recording(sse_stream_mock([]))
        self.client.set_cookie("ai_summary_server", "http://untrusted.example.org:11434")

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([("http://untrusted.example.org:11434", "")], calls)

    def test_endpoint_ignores_credentials_in_user_server(self):
        # httpx would turn the userinfo into an Authorization header; the
        # preference is ignored and the admin's server is used instead
        self.setattr4test(searx.get_setting("ai_summary"), "api_key", "sk-secret")
        calls = self.mock_upstream_recording(sse_stream_mock([]))
        self.client.set_cookie("ai_summary_server", "http://user:pass@untrusted.example.org:11434")

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([(BASE_URL, "sk-secret")], calls)

    def test_endpoint_sends_the_users_key_to_the_users_server(self):
        self.setattr4test(searx.get_setting("ai_summary"), "api_key", "sk-secret")
        calls = self.mock_upstream_recording(sse_stream_mock([]))
        self.client.set_cookie("ai_summary_server", "http://192.168.1.10:11434")
        self.client.set_cookie("ai_summary_api_key", "sk-users-own")

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([("http://192.168.1.10:11434", "sk-users-own")], calls)

    def test_api_key_is_not_part_of_the_preferences_url(self):
        # users copy the preferences URL around to transfer/share their
        # settings -- a credential must not travel with it
        self.pref.parse_dict({"ai_summary_api_key": "sk-users-own"})
        self.assertEqual("sk-users-own", self.pref.get_value("ai_summary_api_key"))

        blob = self.pref.get_as_url_params()
        decoded = decompress(urlsafe_b64decode(blob)).decode()
        self.assertNotIn("sk-users-own", decoded)
        self.assertNotIn("ai_summary_api_key", decoded)
        # a non-secret preference of the same tab is still included
        self.assertIn("ai_summary_model", decoded)

    def test_preferences_tab_hidden_when_plugin_not_activated(self):
        # the global STORAGE is what the preferences view renders from; in the
        # default settings the ai_summary plugin is not activated
        res = self.client.get("/preferences")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn('tab-label-ai"', res.data.decode())

    def test_preferences_tab_shown_when_plugin_activated(self):
        self.setattr4test(searx.plugins, "STORAGE", self.storage)
        res = self.client.get("/preferences")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode()
        self.assertIn('tab-label-ai"', html)
        self.assertIn("ai_summary_api_key", html)

    def test_endpoint_retries_a_server_that_does_not_answer(self):
        # a cold LLM server loads the model before it answers anything, which
        # can outlast read_timeout; the retry is what makes the first search
        # after an idle period work
        import httpx  # pylint: disable=import-outside-toplevel

        attempts = []
        ok = sse_stream_mock([{"choices": [{"delta": {"content": "hi"}}]}])

        @contextmanager
        def stream(*_args, **_kwargs):
            attempts.append(1)
            if len(attempts) == 1:
                raise httpx.ReadTimeout("timed out")
            with ok.stream() as resp:
                yield resp

        client_mock = Mock()
        client_mock.stream = stream
        self.mock_upstream(client_mock)

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(attempts))
        lines = [json.loads(line) for line in res.data.decode().splitlines() if line]
        self.assertEqual(lines[0], {"delta": "hi"})

    def test_endpoint_gives_up_after_the_retry(self):
        import httpx  # pylint: disable=import-outside-toplevel

        attempts = []

        @contextmanager
        def stream(*_args, **_kwargs):
            attempts.append(1)
            raise httpx.ConnectTimeout("nope")
            yield  # pylint: disable=unreachable

        client_mock = Mock()
        client_mock.stream = stream
        self.mock_upstream(client_mock)

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 502)
        self.assertEqual(2, len(attempts))

    def test_endpoint_does_not_retry_a_client_error(self):
        # a wrong API key or an unknown model does not fix itself
        attempts = []
        bad = sse_stream_mock([], status_code=401)

        @contextmanager
        def stream(*_args, **_kwargs):
            attempts.append(1)
            with bad.stream() as resp:
                yield resp

        client_mock = Mock()
        client_mock.stream = stream
        self.mock_upstream(client_mock)

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 502)
        self.assertEqual(1, len(attempts))

    def test_endpoint_retries_a_server_error(self):
        # 5xx means "not right now" -- e.g. a model that is still loading;
        # this is the failure that arrives immediately instead of timing out
        attempts = []
        ok = sse_stream_mock([{"choices": [{"delta": {"content": "hi"}}]}])
        bad = sse_stream_mock([], status_code=503)

        @contextmanager
        def stream(*_args, **_kwargs):
            attempts.append(1)
            src = bad if len(attempts) == 1 else ok
            with src.stream() as resp:
                yield resp

        client_mock = Mock()
        client_mock.stream = stream
        self.mock_upstream(client_mock)

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(2, len(attempts))
        lines = [json.loads(line) for line in res.data.decode().splitlines() if line]
        self.assertEqual(lines[0], {"delta": "hi"})

    def test_endpoint_upstream_error(self):
        self.mock_upstream(sse_stream_mock([], status_code=500))

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 502)

    def test_endpoint_error_while_streaming(self):
        upstream = Mock(status_code=200)
        upstream.iter_lines.return_value = iter(
            ['data: {"choices": [{"delta": {"content": "Hello"}}]}', "data: this is not json"]
        )

        @contextmanager
        def stream(*_args, **_kwargs):
            yield upstream

        client_mock = Mock()
        client_mock.stream = stream
        self.mock_upstream(client_mock)

        res = self.client.post("/ai_summary", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(res.status_code, 200)
        lines = [json.loads(line) for line in res.data.decode().splitlines() if line]
        self.assertEqual(lines[0], {"delta": "Hello"})
        self.assertEqual(lines[1], {"done": True, "error": "upstream error"})
