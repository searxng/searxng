from searx.result_types import Answer, Translations
from searx.answerers import Answerer, AnswererInfo
from searx.result_types.answer import BaseAnswer
from searx.extended_types import SXNG_Response
from flask_babel import gettext as _
from flask_babel import get_locale
from searx.network import get

from searx.result_types import EngineResults
from . import Plugin, PluginInfo


from dataclasses import dataclass, field
from typing import List, Optional
from html import unescape
from urllib import parse
import typing
import re

if typing.TYPE_CHECKING:
    from searx.extended_types import SXNG_Request
    from searx.search import SearchWithPlugins
    from . import PluginCfg



# ---------------------------------------  Definition Provider Functionality  ------------------------------------------

@dataclass(eq=True, frozen=False)
class Definition:
    """
    Root data model for a single definition entry
    """

    word:           str
    part_of_speech: Optional[str]
    definition:     str
    examples:       List[str] = field(default_factory=list)
    lang:           str = "unknown"
    provider:       str = "unknown"
    source_url:     Optional[str] = None


    # Part-of-speech normalization
    pos_normalized = {
        "noun":         "noun",
        "verb":         "verb",
        "adjective":    "adjective",
        "adverb":       "adverb",
        "pronoun":      "pronoun",
        "preposition":  "preposition",
        "conjunction":  "conjunction",
        "interjection": "interjection",
        "proper noun":  "proper noun",
        "proper_noun":  "proper noun",
        "determiner":   "determiner",
        "article":      "article",
    }

    # Normalize fields & dedupe examples when created
    def __post_init__(self):
        self.word       = self._clean_text(self.word)
        self.definition = self._clean_text(self.definition)
        self.examples   = self._dedupe(self.examples)

        pos = (self.part_of_speech or "").strip().lower()
        self.part_of_speech = self.pos_normalized.get(pos, pos or "unknown")

    def _clean_text(self, s: str) -> str:
        s = unescape(s or "")
        return " ".join(s.split())

    def _dedupe(self, seq: List[str]) -> List[str]:
        seen, out = set(), []
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
    def dedupe_key(self) -> tuple:
        return (self.normalized_pos, self.definition)

    def short_example(self, limit: int = 140) -> Optional[str]:
        if not self.examples:
            return None

        ex = self.examples[0]
        return (ex if len(ex) <= limit else ex[: max(0, limit - 1)] + "…")


class DefinitionProvider():
    """
    Root class for handling web IO and exposing a common interface.
    Subclasses should implement `.definitions(word, lang="en") -> List[Definition]`.
    """

    # Override this
    name: str


    def _get(self, url: str) -> SXNG_Response:
        return get(url)

    def lookup(self, term: str, lang: str = "en") -> List[Definition]:
        """
        Return a list of Definition objects for `word`
        Must be implemented by subclasses
        """
        raise NotImplementedError


class WiktionaryProvider(DefinitionProvider):
    """
    Wiktionary implementation using the official REST API:
    https://en.wiktionary.org/api/rest_v1/
    """

    name:          str = 'wiktionary'
    api_template:  str = "https://en.wiktionary.org/api/rest_v1/page/definition/{title}"
    page_template: str = "https://en.wiktionary.org/wiki/{title}"

    # Matches href="/wiki/term#POS"
    _wiki_href_re = re.compile(r'href="(?P<href>/wiki/[^"]+)"')

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
            path = href.split('#', 1)[0]
            if path.startswith('/wiki/'):
                path = path[len('/wiki/'):]
            path = path.split(':', 1)[0]

            term = parse.unquote(path).replace('_', ' ').strip()
            return term

        def _repl(m: re.Match) -> str:
            term = _normalize(m.group('href'))
            if not term:
                return 'href="#"'
            q = parse.quote_plus(f'{keyword} {term}').lower()
            return f'href="/search?q={q}"'

        return self._wiki_href_re.sub(_repl, html)


    def lookup(self, term: str, lang: str = "en") -> List[Definition]:
        url  = self.api_template.format(title=term)
        resp = None

        try:
            resp = self._get(url)
            success = resp.status_code == 200
        except:
            success = False

        if not (success and resp):
            return []

        payload = resp.json()
        entries = payload.get(lang, [])
        results: List[Definition] = []

        for entry in entries:
            pos = entry.get("partOfSpeech")
            for d in entry.get("definitions", []):
                def_html = self._rewrite_wiki_links(d.get("definition", ""))
                ex_list  = [self._rewrite_wiki_links(x) for x in d.get("examples", [])]
                results.append(

                    Definition(
                        word           = term,
                        part_of_speech = pos,
                        definition     = def_html,
                        examples       = ex_list,
                        lang           = lang,
                        provider       = "wiktionary",
                        source_url     = self.page_template.format(title=term),
                    )

                )

        return results



# ----------------------------------------------  SearXNG Integration  -------------------------------------------------

class DefineHandler():
    """
    Links a definition provider and provides a public API to the answerer
    """

    keyword:  str = "define"
    provider: DefinitionProvider = WiktionaryProvider()

    default_answer: Answer = Answer(answer=_("No definitions were found."))
    max_definitions:   int = 5
    max_examples:      int = 3


    def _get_locale(self) -> str:
        """
        Prefer the user's selected search language if available
        otherwise fall back to the UI locale, finally 'en'
        Returns a ISO code like 'en', 'fr', 'de'
        """

        loc = get_locale()
        if loc:
            return str(loc).split('_')[0].lower()

        return 'en'


    # Expects a full query, including 'self.keyword'
    def _extract_term(self, query: str) -> str | None:
        extracted = None
        term_key  = self.keyword + ' '

        if query.startswith(term_key):
            extracted = query[len(term_key):].strip()

        return extracted


    def _make_definitions_answer(self, definitions: list[Translations.Item], url: str | None) -> Translations:
        if not self.provider.name:
            raise NotImplementedError('no real provider was specified')

        return Translations(
            translations = definitions,
            url          = url,
            engine       = self.provider.name,
            template     = 'answer/define.html'
        )


    def _build_translations_answer(self, definitions: List[Definition]) -> Translations | None:
        """
        Turn a list[Definition] into a single Translations answer
        - One item per part-of-speech
        - Each item carries multiple definitions & a few examples
        """

        if not definitions:
            return None

        by_pos: dict[str, List[Definition]] = {}
        for d in definitions:
            by_pos.setdefault(d.normalized_pos, []).append(d)

        url = next((d.source_url for d in definitions if d.source_url), None)
        items: List[Translations.Item] = []


        # Dedupe identical senses
        for pos, entries in by_pos.items():
            seen = set()
            definitions_text: List[str] = []
            examples: List[str] = []

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
            pos  = entries[0].normalized_pos if entries else "unknown"

            items.append(
                Translations.Item(
                    text            = word,             # now just "liquid"
                    transliteration = f"({pos})" if pos != "unknown" else "",
                    definitions     = definitions_text,
                    examples        = examples,
                    synonyms        = [],
                )
            )

        return self._make_definitions_answer(definitions=items, url=url)


    # Expects a full query, including 'self.keyword'
    def find_results(self, query: str) -> list[BaseAnswer]:
        results = []
        term = self._extract_term(query)
        if not term:
            return results

        lang = self._get_locale()
        definitions: list[Definition] = self.provider.lookup(term, lang=lang)
        if not definitions:
            results.append(self.default_answer)
            return results

        translations_answer = self._build_translations_answer(definitions)
        if translations_answer: results.append(translations_answer)
        else:            results.append(self.default_answer)

        return results


class SXNGPlugin(Plugin, DefineHandler):
    """Adds a 'define <term>' special query that returns a Translations answer."""

    id = DefineHandler.keyword
    keywords = [ id ]

    def __init__(self, plg_cfg: "PluginCfg"):
        Plugin.__init__(self, plg_cfg)

        self.info = PluginInfo(
            id                 = self.id,
            name               = _(self.id.title()),
            description        = f'{_("Displays definitions to a search term")} ({_("Source")}: {self.provider.name})',
            examples           = [ f"{self.id} <{_('term')}>", f"{self.id} effervescence" ],
            preference_section = "query",
        )

    def post_search(self, request: "SXNG_Request", search: "SearchWithPlugins") -> EngineResults:
        """Returns answers only for the first page"""
        
        results = EngineResults()

        if search.search_query.pageno > 1:
            return results

        q = (search.search_query.query or "").strip()
        term = self._extract_term(q)
        if not term:
            return results

        # Pull functionality from 'DefineHandler'
        for ans in self.find_results(q):
            results.add(ans)

        return results
