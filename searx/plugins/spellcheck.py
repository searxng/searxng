# SPDX-License-Identifier: AGPL-3.0-or-later
"""Spell checking plugin providing "Did you mean?" corrections.

This plugin suggests a single corrected variant of the current query
and exposes an on/off toggle in Preferences.

The plugin uses lazy-loaded dictionaries from ``pyspellchecker`` and
supports a limited set of languages. If the UI/search language is not
supported or the query is unchanged, no results are produced.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flask_babel import gettext

from searx.autocomplete import search_autocomplete
from searx.plugins import Plugin, PluginInfo
from searx.result_types import EngineResults

try:
    from spellchecker import SpellChecker  # type: ignore[unresolved-import]
except ImportError:
    SpellChecker = None  # type: ignore[misc]

if TYPE_CHECKING:  # import only for typing
    from collections.abc import Iterable

    from searx.extended_types import SXNG_Request
    from searx.plugins import PluginCfg
    from searx.search import SearchWithPlugins


log: logging.Logger = logging.getLogger("searx.plugins.spellcheck")


@runtime_checkable
class WordCorrectionProvider(Protocol):
    """Provider for per-word spell correction."""

    def find_misspellings(self, candidates: Iterable[str]) -> Iterable[str]:
        """Return misspelled tokens among candidates.

        Parameters
        ----------
        candidates : Iterable[str]
            Candidate tokens to evaluate.

        Returns
        -------
        Iterable[str]
            Tokens detected as misspellings.
        """
        raise NotImplementedError

    def correction(self, word: str) -> str | None:
        """Return the best correction for a single word.

        Parameters
        ----------
        word : str
            Input token to correct.

        Returns
        -------
        str or None
            Suggested correction or ``None`` if unknown.
        """
        raise NotImplementedError


@runtime_checkable
class QuerySuggestionProvider(Protocol):  # pylint: disable=too-few-public-methods
    """Provider for whole-query correction."""

    def correct_query(self, query: str, sxng_locale: str) -> str | None:
        """Return a whole-query suggestion.

        Parameters
        ----------
        query : str
            Original query text.
        sxng_locale : str
            SearXNG locale tag.

        Returns
        -------
        str or None
            Suggested query replacement, or ``None`` if not applicable.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class _SupportedLanguage:
    code: str
    spellchecker_code: str


SUPPORTED_LANGUAGES: tuple[_SupportedLanguage, ...] = (
    _SupportedLanguage("en", "en"),
    _SupportedLanguage("es", "es"),
    _SupportedLanguage("fr", "fr"),
    _SupportedLanguage("pt", "pt"),
    _SupportedLanguage("de", "de"),
    _SupportedLanguage("it", "it"),
    _SupportedLanguage("ru", "ru"),
    _SupportedLanguage("ar", "ar"),
    _SupportedLanguage("eu", "eu"),  # Basque
    _SupportedLanguage("lv", "lv"),
    _SupportedLanguage("nl", "nl"),
)


_LANG_MAP: dict[str, str] = {lang.code: lang.spellchecker_code for lang in SUPPORTED_LANGUAGES}


@lru_cache(maxsize=16)
def _load_spellchecker(lang_code: str):
    """Lazily load a ``SpellChecker`` for the given language.

    Parameters
    ----------
    lang_code : str
        Language code as expected by ``pyspellchecker``.

    Returns
    -------
    object | None
        The SpellChecker instance or None if unavailable.
    """
    if SpellChecker is None:
        log.warning("pyspellchecker is not installed")
        return None

    try:
        return SpellChecker(language=lang_code)
    except (OSError, ValueError, LookupError) as exc:
        log.warning("pyspellchecker failed to initialize for language %s: %s", lang_code, exc)
        return None


class PySpellcheckerProvider:
    """Spellcheck provider using ``pyspellchecker``.

    Parameters
    ----------
    lang_code : str
        Language code for the underlying dictionary.
    """

    def __init__(self, lang_code: str):
        self._sc = _load_spellchecker(lang_code)

    def find_misspellings(self, candidates: Iterable[str]) -> Iterable[str]:  # type: ignore[override]
        """Return misspelled items from candidates.

        Parameters
        ----------
        candidates : Iterable[str]
            Candidate tokens to evaluate.

        Returns
        -------
        Iterable[str]
            Misspelled tokens among ``candidates``. Returns an empty
            iterable if the backend is unavailable.
        """
        if not self._sc:
            return []
        func = getattr(self._sc, "unknown", None)
        if not callable(func):
            return []
        return func(candidates)  # pylint: disable=not-callable

    def correction(self, word: str) -> str | None:  # type: ignore[override]
        """Return the best correction for ``word``.

        Parameters
        ----------
        word : str
            Input token to correct.

        Returns
        -------
        str or None
            Suggested correction or ``None`` when no improvement is found
            or the backend is unavailable.
        """
        if not self._sc:
            return None
        func = getattr(self._sc, "correction", None)
        if not callable(func):
            return None
        return func(word)  # pylint: disable=not-callable


class GoogleAutocompleteProvider:
    """Spellcheck provider backed by Google Autocomplete.

    Implements optional ``correct_query``; word-level methods are no-ops.
    """

    def find_misspellings(self, _candidates: Iterable[str]) -> Iterable[str]:
        """Return an empty iterable; Google provider does not check words.

        Parameters
        ----------
        _candidates : Iterable[str]
            Ignored.

        Returns
        -------
        Iterable[str]
            Always returns an empty iterable.
        """
        return []

    def correction(self, _word: str) -> str | None:
        """Return ``None``; Google provider does not correct single words.

        Parameters
        ----------
        _word : str
            Ignored.

        Returns
        -------
        str or None
            Always returns ``None``.
        """
        return None

    def correct_query(self, query: str, sxng_locale: str) -> str | None:
        """Return a whole-query suggestion from Google Autocomplete.

        Parameters
        ----------
        query : str
            Original query text.
        sxng_locale : str
            SearXNG locale tag (influences Google subdomain/language).

        Returns
        -------
        str or None
            Suggested query if sufficiently similar and different;
            otherwise ``None``.
        """

        suggestions = search_autocomplete("google", query, sxng_locale) or []
        if not suggestions:
            return None

        # Pick the suggestion with the best combined score:
        # similarity minus a small penalty for length difference, with
        # an additional bonus for permutations of the same letters
        # (common transposition errors like "teh" -> "the").
        best: tuple[float, str] | None = None
        for s in suggestions:
            similarity = SequenceMatcher(None, query, s).ratio()
            penalty = 0.1 * abs(len(s) - len(query))
            score = similarity - penalty
            if sorted(s) == sorted(query):
                score += 0.1
            if best is None or score > best[0]:  # pylint: disable=unsubscriptable-object
                best = (score, s)

        # Conservative acceptance threshold
        if not best or best[0] < 0.5:
            return None
        candidate = best[1]
        if candidate.strip() == query.strip():
            return None
        return candidate


def _tokenize(text: str) -> list[tuple[str, bool]]:
    """Tokenize text into a sequence of (token, is_word) keeping delimiters.

    Parameters
    ----------
    text : str
        Original query text.

    Returns
    -------
    list[tuple[str, bool]]
        Sequence of (segment, is_word) preserving whitespace segments.
    """
    # Use a simple split that preserves delimiters; avoid heavy NLP here.
    # Split on whitespace while capturing separators.
    parts: list[str] = re.split(r"(\s+)", text)
    tokens: list[tuple[str, bool]] = []
    for p in parts:
        if not p:
            continue
        tokens.append((p, p.strip() != "" and not p.isspace()))
    return tokens


def _is_supported_lang(pref_lang: str | None) -> str | None:
    """Map preference language to spellchecker language code if supported.

    Parameters
    ----------
    pref_lang : str or None
        Preference language (e.g., 'en', 'de', 'all', 'auto', '').

    Returns
    -------
    str or None
        Spellchecker language code or ``None`` if unsupported.
    """
    if not pref_lang:
        return None
    pref = pref_lang.lower()
    if pref in ("all", "auto"):
        return None
    # Normalize regional variants like en-US -> en
    base = pref.split("-")[0]
    return _LANG_MAP.get(base)


class SXNGPlugin(Plugin):
    """Spell checking plugin.

    Suggests a corrected query ("Did you mean?") on page 1 when the
    language is supported by the underlying dictionary.
    """

    id = "spellcheck"

    def __init__(self, plg_cfg: PluginCfg) -> None:
        """Initialize the plugin.

        Parameters
        ----------
        plg_cfg : PluginCfg
            The plugin configuration passed from settings.
        """
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id,
            name=gettext("Spell Check"),
            description=gettext("Suggest corrected queries when typos are detected"),
            preference_section="general",
        )
        # provider selection via settings (PluginCfg.parameters)
        params = getattr(plg_cfg, "parameters", {}) or {}
        provider = params.get("provider", "pyspellchecker")
        self.provider_name: str = str(provider)

    def post_search(self, request: SXNG_Request, search: SearchWithPlugins) -> EngineResults:
        """Compute spelling correction suggestions.

        Parameters
        ----------
        request : SXNG_Request
            The current HTTP request with preferences.
        search : SearchWithPlugins
            The running search execution context.

        Returns
        -------
        EngineResults
            Result list containing at most one legacy correction item.
        """
        results = EngineResults()
        corrected = self._get_correction(request, search)

        if corrected is not None:
            results.add(results.types.LegacyResult({"correction": corrected}))

        return results

    def _get_correction(self, request: SXNG_Request, search: SearchWithPlugins) -> str | None:
        """Get spelling correction for the search query.

        Parameters
        ----------
        request : SXNG_Request
            The current HTTP request with preferences.
        search : SearchWithPlugins
            The running search execution context.

        Returns
        -------
        str or None
            Corrected query if available, otherwise None.
        """
        # Only check on first page
        if search.search_query.pageno > 1:
            return None

        query: str = search.search_query.query or ""
        if not query or len(query) < 2:
            return None

        # Avoid touching bang-prefixed queries at the beginning (!yt ...)
        if query.lstrip().startswith("!"):
            return None

        # Determine spellcheck language
        lang_pref: str | None = request.preferences.get_value("language")
        sc_lang: str | None = _is_supported_lang(lang_pref)
        if sc_lang is None:
            # Fallback: use UI locale if search language is auto/all/unsupported
            ui_locale: str | None = request.preferences.get_value("locale")
            if ui_locale:
                sc_lang = _LANG_MAP.get(ui_locale.split("-")[0].lower())

        if sc_lang is None and self.provider_name != "google":
            return None

        provider = self._select_provider(sc_lang)
        if provider is None:
            return None

        # Get correction from provider
        if isinstance(provider, GoogleAutocompleteProvider):
            corrected = provider.correct_query(query, request.preferences.get_value("locale") or "")
        else:
            corrected = self._correct_query(query, provider)  # type: ignore[arg-type]

        # Return correction only if it's different from original query
        return corrected if corrected and corrected != query else None

    # --- helpers -----------------------------------------------------------------

    def _correct_query(self, query: str, spellchecker: WordCorrectionProvider) -> str | None:
        """Return a single corrected variant of the query or ``None``.

        Parameters
        ----------
        query : str
            Original query text.
        spellchecker : SpellcheckProvider
            Provider implementing per-word correction.

        Returns
        -------
        str or None
            Corrected query if different and meaningful; otherwise ``None``.
        """
        # We operate token-wise, only alphabetic words. Keep delimiters.
        tokens: list[tuple[str, bool]] = _tokenize(query)
        words: list[str] = [t for t, is_word in tokens if is_word]
        if not words:
            return None

        # Determine misspelled words first to avoid unnecessary corrections.
        misspelled: set[str] = set(spellchecker.find_misspellings(words))
        if not misspelled:
            return None

        corrected_parts: list[str] = []
        for part, is_word in tokens:
            if not is_word:
                corrected_parts.append(part)
                continue
            w = part
            # Preserve casing of the first letter when applying correction.
            lower_w = w.lower()
            if lower_w in misspelled:
                suggestion = spellchecker.correction(lower_w)
                if suggestion and suggestion != lower_w:
                    if w[0].isupper():
                        suggestion = suggestion.capitalize()
                    w = suggestion
            corrected_parts.append(w)

        corrected_query = "".join(corrected_parts)
        # Avoid trivial/no-op changes
        if corrected_query.strip() == query.strip():
            return None
        return corrected_query

    def _select_provider(self, sc_lang: str | None) -> object | None:
        """Select and initialize a provider based on configuration.

        Parameters
        ----------
        sc_lang : str or None
            Spellchecker language code for dictionary-backed providers.

        Returns
        -------
        SpellcheckProvider or None
            A provider instance or ``None`` when it cannot be constructed.
        """
        name = (self.provider_name or "pyspellchecker").lower()
        if name == "google":
            return GoogleAutocompleteProvider()
        # default: pyspellchecker requires language
        if sc_lang is None:
            return None
        return PySpellcheckerProvider(sc_lang)
