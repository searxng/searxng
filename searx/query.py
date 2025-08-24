# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name, missing-module-docstring, missing-class-docstring

from abc import abstractmethod, ABC
import re

from searx import settings
from searx.sxng_locales import sxng_locales
from searx.engines import categories, engines, engine_shortcuts
from searx.external_bang import get_bang_definition_and_autocomplete
from searx.search.models import EngineRef
from searx.webutils import VALID_LANGUAGE_CODE


class QueryPartParser(ABC):

    __slots__ = "raw_text_query", "enable_autocomplete"

    @staticmethod
    @abstractmethod
    def check(raw_value):
        """Check if raw_value can be parsed"""

    def __init__(self, raw_text_query, enable_autocomplete):
        self.raw_text_query = raw_text_query
        self.enable_autocomplete = enable_autocomplete

    @abstractmethod
    def __call__(self, raw_value):
        """Try to parse raw_value: set the self.raw_text_query properties

        return True if raw_value has been parsed

        self.raw_text_query.autocomplete_list is also modified
        if self.enable_autocomplete is True
        """

    def _add_autocomplete(self, value):
        if value not in self.raw_text_query.autocomplete_list:
            self.raw_text_query.autocomplete_list.append(value)


class TimeoutParser(QueryPartParser):
    @staticmethod
    def check(raw_value):
        return raw_value[0] == '<'

    def __call__(self, raw_value):
        value = raw_value[1:]
        found = self._parse(value) if len(value) > 0 else False
        if self.enable_autocomplete and not value:
            self._autocomplete()
        return found

    def _parse(self, value):
        if not value.isdigit():
            return False
        raw_timeout_limit = int(value)
        if raw_timeout_limit < 100:
            # below 100, the unit is the second ( <3 = 3 seconds timeout )
            self.raw_text_query.timeout_limit = float(raw_timeout_limit)
        else:
            # 100 or above, the unit is the millisecond ( <850 = 850 milliseconds timeout )
            self.raw_text_query.timeout_limit = raw_timeout_limit / 1000.0
        return True

    def _autocomplete(self):
        for suggestion in ['<3', '<850']:
            self._add_autocomplete(suggestion)


class LanguageParser(QueryPartParser):
    @staticmethod
    def check(raw_value):
        return raw_value[0] == ':'

    def __call__(self, raw_value):
        value = raw_value[1:].lower().replace('_', '-')
        found = self._parse(value) if len(value) > 0 else False
        if self.enable_autocomplete and not found:
            self._autocomplete(value)
        return found

    def _parse(self, value):
        found = False
        # check if any language-code is equal with
        # declared language-codes
        for lc in sxng_locales:
            lang_id, lang_name, country, english_name, _flag = map(str.lower, lc)

            # if correct language-code is found
            # set it as new search-language

            if (
                value == lang_id or value == lang_name or value == english_name or value.replace('-', ' ') == country
            ) and value not in self.raw_text_query.languages:
                found = True
                lang_parts = lang_id.split('-')
                if len(lang_parts) == 2:
                    self.raw_text_query.languages.append(lang_parts[0] + '-' + lang_parts[1].upper())
                else:
                    self.raw_text_query.languages.append(lang_id)
                # to ensure best match (first match is not necessarily the best one)
                if value == lang_id:
                    break

        # user may set a valid, yet not selectable language
        if VALID_LANGUAGE_CODE.match(value) or value == 'auto':
            lang_parts = value.split('-')
            if len(lang_parts) > 1:
                value = lang_parts[0].lower() + '-' + lang_parts[1].upper()
            if value not in self.raw_text_query.languages:
                self.raw_text_query.languages.append(value)
                found = True

        return found

    def _autocomplete(self, value):
        if not value:
            # show some example queries
            if len(settings['search']['languages']) < 10:
                for lang in settings['search']['languages']:
                    self.raw_text_query.autocomplete_list.append(':' + lang)
            else:
                for lang in [":en", ":en_us", ":english", ":united_kingdom"]:
                    self.raw_text_query.autocomplete_list.append(lang)
            return

        for lc in sxng_locales:
            if lc[0] not in settings['search']['languages']:
                continue
            lang_id, lang_name, country, english_name, _flag = map(str.lower, lc)

            # check if query starts with language-id
            if lang_id.startswith(value):
                if len(value) <= 2:
                    self._add_autocomplete(':' + lang_id.split('-')[0])
                else:
                    self._add_autocomplete(':' + lang_id)

            # check if query starts with language name
            if lang_name.startswith(value) or english_name.startswith(value):
                self._add_autocomplete(':' + lang_name)

            # check if query starts with country
            # here "new_zealand" is "new-zealand" (see __call__)
            if country.startswith(value.replace('-', ' ')):
                self._add_autocomplete(':' + country.replace(' ', '_'))


class ExternalBangParser(QueryPartParser):
    @staticmethod
    def check(raw_value):
        return raw_value.startswith('!!') and len(raw_value) > 2

    def __call__(self, raw_value):
        value = raw_value[2:].lower()
        found, bang_ac_list = self._parse(value) if len(value) > 0 else (False, [])
        if self.enable_autocomplete:
            self._autocomplete(bang_ac_list)
        return found

    def _parse(self, value):
        found = False
        bang_definition, bang_ac_list = get_bang_definition_and_autocomplete(value)
        if bang_definition is not None:
            self.raw_text_query.external_bang = value
            found = True
        return found, bang_ac_list

    def _autocomplete(self, bang_ac_list):
        if not bang_ac_list:
            bang_ac_list = ['g', 'ddg', 'bing']
        for external_bang in bang_ac_list:
            self._add_autocomplete('!!' + external_bang)


class BangParser(QueryPartParser):
    @staticmethod
    def check(raw_value):
        # make sure it's not any bang with double '!!'
        return raw_value[0] == '!' and (len(raw_value) < 2 or raw_value[1] != '!')

    def __call__(self, raw_value):
        value = raw_value[1:].replace('-', ' ').replace('_', ' ').lower()
        found = self._parse(value) if len(value) > 0 else False
        if found and raw_value[0] == '!':
            self.raw_text_query.specific = True
        if self.enable_autocomplete:
            self._autocomplete(raw_value[0], value)
        return found

    def _parse(self, value):
        # check if prefix is equal with engine shortcut
        if value in engine_shortcuts:  # pylint: disable=consider-using-get
            value = engine_shortcuts[value]

        # check if prefix is equal with engine name
        if value in engines:
            self.raw_text_query.enginerefs.append(EngineRef(value, 'none'))
            return True

        # check if prefix is equal with category name
        if value in categories:
            # using all engines for that search, which
            # are declared under that category name
            self.raw_text_query.enginerefs.extend(
                EngineRef(engine.name, value)
                for engine in categories[value]
                if (engine.name, value) not in self.raw_text_query.disabled_engines
            )
            return True

        return False

    def _autocomplete(self, first_char, value):
        if not value:
            # show some example queries
            for suggestion in ['images', 'wikipedia', 'osm']:
                if suggestion not in self.raw_text_query.disabled_engines or suggestion in categories:
                    self._add_autocomplete(first_char + suggestion)
            return

        # check if query starts with category name
        for category in categories:
            if category.startswith(value):
                self._add_autocomplete(first_char + category.replace(' ', '_'))

        # check if query starts with engine name
        for engine in engines:
            if engine.startswith(value):
                self._add_autocomplete(first_char + engine.replace(' ', '_'))

        # check if query starts with engine shortcut
        for engine_shortcut in engine_shortcuts:
            if engine_shortcut.startswith(value):
                self._add_autocomplete(first_char + engine_shortcut)


class FeelingLuckyParser(QueryPartParser):
    @staticmethod
    def check(raw_value):
        return raw_value == '!!'

    def __call__(self, raw_value):
        self.raw_text_query.redirect_to_first_result = True
        return True


class RawTextQuery:
    """parse raw text query (the value from the html input)"""

    PARSER_CLASSES = [
        TimeoutParser,  # force the timeout
        LanguageParser,  # force a language
        ExternalBangParser,  # external bang (must be before BangParser)
        BangParser,  # force an engine or category
        FeelingLuckyParser,  # redirect to the first link in the results list
    ]

    def __init__(self, query: str, disabled_engines: list):
        assert isinstance(query, str)
        # input parameters
        self.query = query
        self.disabled_engines = disabled_engines if disabled_engines else []
        # parsed values
        self.enginerefs = []
        self.languages = []
        self.timeout_limit = None
        self.external_bang = None
        self.specific = False
        self.autocomplete_list = []
        # internal properties
        self.query_parts = []  # use self.getFullQuery()
        self.user_query_parts = []  # use self.getQuery()
        self.autocomplete_location = None
        self.redirect_to_first_result = False
        self._parse_query()

    def _parse_query(self):
        """
        parse self.query, if tags are set, which
        change the search engine or search-language
        """

        # split query, including whitespaces
        raw_query_parts = re.split(r'(\s+)', self.query)

        last_index_location = None
        autocomplete_index = len(raw_query_parts) - 1

        for i, query_part in enumerate(raw_query_parts):
            # part does only contain spaces, skip
            if query_part.isspace() or query_part == '':
                continue

            # parse special commands
            special_part = False
            for parser_class in RawTextQuery.PARSER_CLASSES:
                if parser_class.check(query_part):
                    special_part = parser_class(self, i == autocomplete_index)(query_part)
                    break

            # append query part to query_part list
            qlist = self.query_parts if special_part else self.user_query_parts
            qlist.append(query_part)
            last_index_location = (qlist, len(qlist) - 1)

        self.autocomplete_location = last_index_location

    def get_autocomplete_full_query(self, text):
        qlist, position = self.autocomplete_location
        qlist[position] = text
        return self.getFullQuery()

    def changeQuery(self, query):
        self.user_query_parts = query.strip().split()
        self.query = self.getFullQuery()
        self.autocomplete_location = (self.user_query_parts, len(self.user_query_parts) - 1)
        self.autocomplete_list = []
        return self

    def getQuery(self):
        return ' '.join(self.user_query_parts)

    def getFullQuery(self):
        """
        get full query including whitespaces
        """
        return '{0} {1}'.format(' '.join(self.query_parts), self.getQuery()).strip()

    def __str__(self):
        return self.getFullQuery()

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            + f"query={self.query!r} "
            + f"disabled_engines={self.disabled_engines!r}\n  "
            + f"languages={self.languages!r} "
            + f"timeout_limit={self.timeout_limit!r} "
            + f"external_bang={self.external_bang!r} "
            + f"specific={self.specific!r} "
            + f"enginerefs={self.enginerefs!r}\n  "
            + f"autocomplete_list={self.autocomplete_list!r}\n  "
            + f"query_parts={self.query_parts!r}\n  "
            + f"user_query_parts={self.user_query_parts!r} >\n"
            + f"redirect_to_first_result={self.redirect_to_first_result!r}"
        )
