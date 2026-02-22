# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the spellcheck plugin."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import patch

from parameterized import parameterized

from searx.plugins.spellcheck import (
    GoogleAutocompleteProvider,
    PySpellcheckerProvider,
    SXNGPlugin,
    _is_supported_lang,
    _tokenize,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

# ---- helpers -------------------------------------------------------------------


@dataclass
class _FakePreferences:
    language: str | None = None
    locale: str | None = "en-US"

    def get_value(self, key: str) -> str | None:  # noqa: D401
        """Return stored preference value by key."""

        if key == "language":
            return self.language
        if key == "locale":
            return self.locale
        return None


@dataclass
class _FakeRequest:
    preferences: _FakePreferences


def _make_request(language: str | None = None, locale: str | None = "en-US") -> _FakeRequest:
    return _FakeRequest(preferences=_FakePreferences(language=language, locale=locale))


def _make_search(query: str, pageno: int = 1):
    return SimpleNamespace(search_query=SimpleNamespace(query=query, pageno=pageno))


class _FakeWordProvider:
    """Simple provider for per-word testing."""

    def __init__(self, misspelled: set[str], mapping: dict[str, str]):
        self._misspelled = misspelled
        self._mapping = mapping

    def find_misspellings(self, candidates: Iterable[str]) -> Iterable[str]:
        return [w for w in candidates if w.lower() in self._misspelled]

    def correction(self, word: str) -> str | None:
        return self._mapping.get(word.lower())


# ---- unit tests ----------------------------------------------------------------


@parameterized.expand(
    [
        ("en", "en"),
        ("en-US", "en"),
        ("de", "de"),
        ("auto", None),
        ("all", None),
        ("", None),
        (None, None),
        ("xx", None),
    ]
)
def test_is_supported_lang(pref: str | None, expected: str | None):
    assert _is_supported_lang(pref) == expected


@parameterized.expand(
    [
        ("hello, world", [("hello,", True), (" ", False), ("world", True)]),
        (
            " one  two ",
            [(" ", False), ("one", True), ("  ", False), ("two", True), (" ", False)],
        ),
        ("a", [("a", True)]),
        ("", []),
    ]
)
def test_tokenize(text: str, expected: list[tuple[str, bool]]):
    assert _tokenize(text) == expected


def test_google_no_suggestions():
    provider = GoogleAutocompleteProvider()
    with patch("searx.plugins.spellcheck.search_autocomplete", return_value=[]):
        assert provider.correct_query("teh", "en-US") is None


def test_google_close_match():
    provider = GoogleAutocompleteProvider()
    with patch(
        "searx.plugins.spellcheck.search_autocomplete",
        return_value=["the", "tech", "ten"],
    ):
        # get_close_matches prefers the closest suggestion
        assert provider.correct_query("teh", "en-US") == "the"


def test_pyspell_provider_backend():
    fake = _FakeWordProvider(misspelled={"recieve"}, mapping={"recieve": "receive"})
    with patch.object(PySpellcheckerProvider, "__init__", return_value=None):
        p = PySpellcheckerProvider.__new__(PySpellcheckerProvider)  # type: ignore[misc]
        # Inject fake backend object
        object.__setattr__(
            p,
            "_sc",
            type(
                "_B",
                (),
                {"unknown": fake.find_misspellings, "correction": fake.correction},
            )(),
        )
        # unknown path
        assert list(p.find_misspellings(["recieve", "x"])) == ["recieve"]
        # correction path
        assert p.correction("recieve") == "receive"


def test_plugin_google_flow():
    cfg = SimpleNamespace(parameters={"provider": "google"})
    plugin = SXNGPlugin(cfg)

    # Suggestion available from provider
    with patch.object(GoogleAutocompleteProvider, "correct_query", return_value="vacuum cleaners"):
        results = plugin.post_search(
            request=_make_request(language=None, locale="en-US"),
            search=_make_search("vacum cleaners", 1),
        )
        assert len(results) == 1
        item = results[0]
        assert isinstance(item, dict)
        assert item.get("correction") == "vacuum cleaners"


def test_plugin_pyspell_fallback():
    cfg = SimpleNamespace(parameters={"provider": "pyspellchecker"})
    plugin = SXNGPlugin(cfg)

    # Force provider selection to our fake provider with fallback language from UI locale
    fake_provider = _FakeWordProvider(misspelled={"recieve"}, mapping={"recieve": "receive"})
    with patch("searx.plugins.spellcheck.PySpellcheckerProvider", return_value=fake_provider):
        results = plugin.post_search(
            request=_make_request(language="auto", locale="en-US"),
            search=_make_search("how to recieve email", 1),
        )
        assert len(results) == 1
        assert results[0]["correction"].startswith("how to receive")


@parameterized.expand([(2, "teh"), (1, ""), (1, "!")])  # not first page  # empty  # bang query
def test_plugin_early_exits(pageno: int, query: str):
    cfg = SimpleNamespace(parameters={"provider": "google"})
    plugin = SXNGPlugin(cfg)

    with patch.object(GoogleAutocompleteProvider, "correct_query", return_value="the"):
        results = plugin.post_search(
            request=_make_request(locale="en-US"),
            search=_make_search(query, pageno),
        )
        assert len(results) == 0
