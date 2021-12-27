# SPDX-License-Identifier: AGPL-3.0-or-later

import typing


class EngineRef:
    """Reference by names to an engine and category"""

    __slots__ = 'name', 'category'

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category

    def __repr__(self):
        return "EngineRef({!r}, {!r})".format(self.name, self.category)

    def __eq__(self, other):
        return self.name == other.name and self.category == other.category

    def __hash__(self):
        return hash((self.name, self.category))


class SearchQuery:
    """container for all the search parameters (query, language, etc...)"""

    __slots__ = (
        'query',
        'engineref_list',
        'lang',
        'safesearch',
        'pageno',
        'time_range',
        'timeout_limit',
        'external_bang',
        'engine_data',
    )

    def __init__(
        self,
        query: str,
        engineref_list: typing.List[EngineRef],
        lang: str = 'all',
        safesearch: int = 0,
        pageno: int = 1,
        time_range: typing.Optional[str] = None,
        timeout_limit: typing.Optional[float] = None,
        external_bang: typing.Optional[str] = None,
        engine_data: typing.Optional[typing.Dict[str, str]] = None,
    ):
        self.query = query
        self.engineref_list = engineref_list
        self.lang = lang
        self.safesearch = safesearch
        self.pageno = pageno
        self.time_range = time_range
        self.timeout_limit = timeout_limit
        self.external_bang = external_bang
        self.engine_data = engine_data or {}

    @property
    def categories(self):
        return list(set(map(lambda engineref: engineref.category, self.engineref_list)))

    def __repr__(self):
        return "SearchQuery({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.query,
            self.engineref_list,
            self.lang,
            self.safesearch,
            self.pageno,
            self.time_range,
            self.timeout_limit,
            self.external_bang,
        )

    def __eq__(self, other):
        return (
            self.query == other.query
            and self.engineref_list == other.engineref_list
            and self.lang == other.lang
            and self.safesearch == other.safesearch
            and self.pageno == other.pageno
            and self.time_range == other.time_range
            and self.timeout_limit == other.timeout_limit
            and self.external_bang == other.external_bang
        )

    def __hash__(self):
        return hash(
            (
                self.query,
                tuple(self.engineref_list),
                self.lang,
                self.safesearch,
                self.pageno,
                self.time_range,
                self.timeout_limit,
                self.external_bang,
            )
        )
