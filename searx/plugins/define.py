# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=too-many-branches, unused-argument, too-few-public-methods
"""
Add a special query ``define <term>`` that returns a compact, inline
definition card powered by Wiktionary.

This plugin parses the query string for the keyword ``define`` (first token),
fetches definitions from the Wiktionary REST API, and renders them using
SearXNG's ``Translations`` answer type and a custom template
(``answer/define.html``). Internal links like ``/wiki/term#Section`` are
rewritten to local SearXNG searches (e.g. ``/search?q=define+term``).

Notes:
- The plugin only returns an answer on the first page of results.
- If the query does not start with ``define ``, the plugin does nothing.
- If no definitions are found, it returns a short 'No definitions were found.'
  answer instead of a Translations card.
- Network calls are made with SearXNG's internal HTTP client.
- ``Translations`` items carry HTML snippets and may need sanitization with other providers.
"""


from dataclasses import dataclass, field
from typing import ClassVar
from html import unescape
from urllib import parse
import typing
import re

from flask_babel import get_locale, gettext  # pyright: ignore[reportUnknownVariableType]

from httpx import HTTPError

from searx.result_types import Answer, Translations
from searx.result_types.answer import BaseAnswer
from searx.extended_types import SXNG_Response
from searx.network import get

from searx.result_types import EngineResults
from . import Plugin, PluginInfo

if typing.TYPE_CHECKING:
    from searx.extended_types import SXNG_Request
    from searx.search import SearchWithPlugins
    from . import PluginCfg


# ---------------------------------------  Definition Provider Functionality  ------------------------------------------


# Internal dataclass for provider results storage
@dataclass(eq=True, frozen=False)
class Definition:
    """
    Root data model for a single definition entry
    """

    word: str
    part_of_speech: str | None
    definition: str
    examples: list[str] = field(default_factory=list)
    lang: str = "unknown"
    provider: str = "unknown"
    source_url: str | None = None

    # Part-of-speech normalization
    pos_normalized: ClassVar[dict[str, str]] = {
        "noun": "noun",
        "verb": "verb",
        "adjective": "adjective",
        "adverb": "adverb",
        "pronoun": "pronoun",
        "preposition": "preposition",
        "conjunction": "conjunction",
        "interjection": "interjection",
        "proper noun": "proper noun",
        "proper_noun": "proper noun",
        "determiner": "determiner",
        "article": "article",
    }

    # Normalize fields & dedupe examples when created
    def __post_init__(self):
        self.word = self._clean_text(self.word)
        self.definition = self._clean_text(self.definition)
        self.examples = self._dedupe(self.examples)

        pos = (self.part_of_speech or "").strip().lower()
        self.part_of_speech = self.pos_normalized.get(pos, pos or "unknown")

    def _clean_text(self, string: str) -> str:
        string = unescape(string or "")
        return " ".join(string.split())

    def _dedupe(self, seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in seq:
            k = self._clean_text(x)
            if k and k not in seen:
                seen.add(k)
                out.append(k)
        return out

    @property
    def normalized_pos(self) -> str:
        return self.part_of_speech or "unknown"

    @property
    def title(self) -> str:
        return f"{self.word} ({self.normalized_pos})" if self.normalized_pos != "unknown" else self.word

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (self.normalized_pos, self.definition)

    def short_example(self, limit: int = 140) -> str | None:
        if not self.examples:
            return None

        ex = self.examples[0]
        return ex if len(ex) <= limit else ex[: max(0, limit - 1)] + "…"


class DefinitionProvider:
    """
    Root class for handling web IO and exposing a common interface.
    Subclasses should implement `.lookup(word, lang="en") -> list[Definition]`.
    """

    # Override this
    name: str = ""

    def _get(self, url: str) -> SXNG_Response:
        return get(url)

    def lookup(self, term: str, lang: str = "en") -> list[Definition]:
        """
        Return a list of Definition objects for `word`
        Must be implemented by subclasses
        """
        why: str = (' ' + term + lang)[0].strip()
        raise NotImplementedError(why)


class WiktionaryProvider(DefinitionProvider):
    """
    Wiktionary implementation using the official REST API:
    https://en.wiktionary.org/api/rest_v1/
    """

    name: str = "wiktionary"
    api_template: str = "https://en.wiktionary.org/api/rest_v1/page/definition/{title}"
    page_template: str = "https://en.wiktionary.org/wiki/{title}"

    # Matches href="/wiki/term#POS"
    _wiki_href_re: re.Pattern[str] = re.compile(r'href="(?P<href>/wiki/[^"]+)"')

    def _rewrite_wiki_links(self, html: str) -> str:
        """
        Rewrites <a href="/wiki/term[#Section][:Index]"> -> /search?q=define+term
        - strips #Part-of-speech fragment
        - strips namespace/index after first colon
        """

        if not html:
            return html

        keyword = DefineHandler.keyword

        def _normalize(href: str) -> str:
            path = href.split("#", 1)[0]
            if path.startswith("/wiki/"):
                path = path[len("/wiki/") :]
            path = path.split(":", 1)[0]

            term = parse.unquote(path).replace("_", " ").strip()
            return term

        def _repl(match: re.Match[str]) -> str:
            term = _normalize(match.group("href"))
            if not term:
                return 'href="#"'
            q = parse.quote_plus(f"{keyword} {term}").lower()
            return f'href="/search?q={q}"'

        return self._wiki_href_re.sub(_repl, html)

    def lookup(self, term: str, lang: str = "en") -> list[Definition]:
        url = self.api_template.format(title=term)
        resp = None

        try:
            resp = self._get(url)
            success = resp.status_code == 200
        except HTTPError:
            success = False

        if not (success and resp):
            return []

        payload = resp.json()
        entries = payload.get(lang, [])
        results: list[Definition] = []

        for entry in entries:
            pos = entry.get("partOfSpeech")
            for d in entry.get("definitions", []):

                raw_def = d.get("definition", "")
                if not raw_def or not raw_def.strip():
                    continue

                def_html = self._rewrite_wiki_links(raw_def)
                ex_list = [self._rewrite_wiki_links(x) for x in d.get("examples", [])]

                if not def_html.strip():
                    continue

                results.append(
                    Definition(
                        word=term,
                        part_of_speech=pos,
                        definition=def_html,
                        examples=ex_list,
                        lang=lang,
                        provider="wiktionary",
                        source_url=self.page_template.format(title=term),
                    )
                )

        return results


# ----------------------------------------------  SearXNG Integration  -------------------------------------------------


class DefineHandler:
    """
    Links a definition provider and provides a public API to the answerer
    """

    keyword: str = "define"
    provider: DefinitionProvider = WiktionaryProvider()

    default_answer: Answer = Answer(answer=gettext("No definitions were found."))
    max_definitions: int = 5
    max_examples: int = 3

    def _get_locale(self) -> str:
        """
        Prefer the user's selected search language if available
        otherwise fall back to the UI locale, finally 'en'
        Returns a ISO code like 'en', 'fr', 'de'
        """

        loc = get_locale()
        if loc:
            return str(loc).split('_', maxsplit=1)[0].lower()

        return "en"

    # Expects a full query, including 'self.keyword'
    def _extract_term(self, query: str) -> str | None:
        extracted = None
        term_key = self.keyword + " "

        if query.startswith(term_key):
            extracted = query[len(term_key) :].strip()

        return extracted

    def _make_definitions_answer(self, definitions: list[Translations.Item], url: str | None) -> Translations:
        if not self.provider.name:
            raise NotImplementedError("no real provider was specified")

        return Translations(
            translations=definitions,
            url=url,
            engine=self.provider.name,
            template="answer/define.html",
        )

    def _build_translations_answer(self, definitions: list[Definition]) -> Translations | None:
        """
        Turn a list[Definition] into a single Translations answer
        - One item per part-of-speech
        - Each item carries multiple definitions & a few examples
        """

        if not definitions:
            return None

        by_pos: dict[str, list[Definition]] = {}
        for d in definitions:
            by_pos.setdefault(d.normalized_pos, []).append(d)

        url = next((d.source_url for d in definitions if d.source_url), None)
        items: list[Translations.Item] = []

        # Dedupe identical senses
        for pos, entries in by_pos.items():
            seen: set[tuple[str, str]] = set()
            definitions_text: list[str] = []
            examples: list[str] = []

            for d in entries:
                if d.dedupe_key in seen:
                    continue

                seen.add(d.dedupe_key)
                if len(definitions_text) < self.max_definitions:
                    definitions_text.append(d.definition)

                for ex in d.examples:
                    if len(examples) >= self.max_examples:
                        break

                    if ex not in examples:
                        examples.append(ex)

            # Title of the card uses the first definition's word
            word = entries[0].word if entries else ""
            pos = entries[0].normalized_pos if entries else "unknown"

            items.append(
                Translations.Item(
                    text=word,
                    transliteration=f"({pos})" if pos != "unknown" else "",
                    definitions=definitions_text,
                    examples=examples,
                    synonyms=[],
                )
            )

        return self._make_definitions_answer(definitions=items, url=url)

    # Expects a full query, including 'self.keyword'
    def find_results(self, query: str) -> list[BaseAnswer]:
        results: list[BaseAnswer] = []
        term: str | None = self._extract_term(query)
        if not term:
            return results

        lang = self._get_locale()
        definitions: list[Definition] = self.provider.lookup(term, lang=lang)
        if not definitions:
            results.append(self.default_answer)
            return results

        translations_answer: Translations | None = self._build_translations_answer(definitions)
        if translations_answer:
            results.append(translations_answer)
        else:
            results.append(self.default_answer)

        return results


class SXNGPlugin(Plugin, DefineHandler):
    """Adds a 'define <term>' special query that returns a Translations answer."""

    id: str = DefineHandler.keyword
    keywords: list[str] = [id]
    info: PluginInfo
    description: str = "Displays definitions to a search term"

    def __init__(self, plg_cfg: "PluginCfg"):
        Plugin.__init__(self, plg_cfg)

        self.info = PluginInfo(
            id=self.id,
            name=gettext(self.id.title()),
            description=f'{gettext(self.description)} ({gettext("Source")}: {self.provider.name})',
            examples=[f"{self.id} <{gettext('term')}>", f"{self.id} effervescence"],
            preference_section="query",
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        """Returns answers only for the first page"""

        results = EngineResults()

        if search.search_query.pageno > 1:
            return results

        query = (search.search_query.query or "").strip()
        term = self._extract_term(query)
        if not term:
            return results

        # Pull functionality from 'DefineHandler'
        for answer in self.find_results(query):
            results.add(answer)

        return results
