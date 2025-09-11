# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

import typing
import babel


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


@typing.final
class SearchQuery:
    """container for all the search parameters (query, language, etc...)"""

    def __init__(
        self,
        query: str,
        engineref_list: list[EngineRef],
        lang: str = 'all',
        safesearch: typing.Literal[0, 1, 2] = 0,
        pageno: int = 1,
        time_range: typing.Literal["day", "week", "month", "year"] | None = None,
        timeout_limit: float | None = None,
        external_bang: str | None = None,
        engine_data: dict[str, dict[str, str]] | None = None,
        redirect_to_first_result: bool | None = None,
    ):  # pylint:disable=too-many-arguments
        self.query = query
        self.engineref_list = engineref_list
        self.lang = lang
        self.safesearch: typing.Literal[0, 1, 2] = safesearch
        self.pageno = pageno
        self.time_range: typing.Literal["day", "week", "month", "year"] | None = time_range
        self.timeout_limit = timeout_limit
        self.external_bang = external_bang
        self.engine_data = engine_data or {}
        self.redirect_to_first_result = redirect_to_first_result

        self.locale = None
        if self.lang:
            try:
                self.locale = babel.Locale.parse(self.lang, sep='-')
            except babel.core.UnknownLocaleError:
                pass

    @property
    def categories(self):
        return list(set(map(lambda engineref: engineref.category, self.engineref_list)))

    def __repr__(self):
        return "SearchQuery({!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.query,
            self.engineref_list,
            self.lang,
            self.safesearch,
            self.pageno,
            self.time_range,
            self.timeout_limit,
            self.external_bang,
            self.redirect_to_first_result,
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
            and self.redirect_to_first_result == other.redirect_to_first_result
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
                self.redirect_to_first_result,
            )
        )

    def __copy__(self):
        return SearchQuery(
            self.query,
            self.engineref_list,
            self.lang,
            self.safesearch,
            self.pageno,
            self.time_range,
            self.timeout_limit,
            self.external_bang,
            self.engine_data,
            self.redirect_to_first_result,
        )
