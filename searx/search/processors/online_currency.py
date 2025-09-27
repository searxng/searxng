# SPDX-License-Identifier: AGPL-3.0-or-later
"""Processor used for ``online_currency`` engines."""

import typing as t

import unicodedata
import re

import flask_babel
import babel

from searx.data import CURRENCIES
from .online import OnlineProcessor, OnlineParams

if t.TYPE_CHECKING:
    from .abstract import EngineProcessor
    from searx.search.models import SearchQuery


search_syntax = re.compile(r".*?(\d+(?:\.\d+)?) ([^.0-9]+) (?:in|to) ([^.0-9]+)", re.I)
"""Search syntax used for from/to currency (e.g. ``10 usd to eur``)"""


class CurrenciesParams(t.TypedDict):
    """Currencies request parameters."""

    amount: float
    """Currency amount to be converted"""

    to_iso4217: str
    """ISO_4217_ alpha code of the currency used as the basis for conversion.

    .. _ISO_4217: https://en.wikipedia.org/wiki/ISO_4217
    """

    from_iso4217: str
    """ISO_4217_ alpha code of the currency to be converted."""

    from_name: str
    """Name of the currency used as the basis for conversion."""

    to_name: str
    """Name of the currency of the currency to be converted."""


class OnlineCurrenciesParams(CurrenciesParams, OnlineParams):  # pylint: disable=duplicate-bases
    """Request parameters of a ``online_currency`` engine."""


class OnlineCurrencyProcessor(OnlineProcessor):
    """Processor class used by ``online_currency`` engines."""

    engine_type: str = "online_currency"

    def get_params(self, search_query: "SearchQuery", engine_category: str) -> OnlineCurrenciesParams | None:
        """Returns a dictionary with the :ref:`request params <engine request
        online_currency>` (:py:obj:`OnlineCurrenciesParams`).  ``None`` is
        returned if the search query does not match :py:obj:`search_syntax`."""

        online_params: OnlineParams | None = super().get_params(search_query, engine_category)

        if online_params is None:
            return None
        m = search_syntax.match(search_query.query)
        if not m:
            return None

        amount_str, from_currency, to_currency = m.groups()
        try:
            amount = float(amount_str)
        except ValueError:
            return None

        # most often $ stands for USD
        if from_currency == "$":
            from_currency = "$ us"

        if to_currency == "$":
            to_currency = "$ us"

        from_iso4217 = from_currency
        if not CURRENCIES.is_iso4217(from_iso4217):
            from_iso4217 = CURRENCIES.name_to_iso4217(_normalize_name(from_currency))

        to_iso4217 = to_currency
        if not CURRENCIES.is_iso4217(to_iso4217):
            to_iso4217 = CURRENCIES.name_to_iso4217(_normalize_name(to_currency))

        if from_iso4217 is None or to_iso4217 is None:
            return None

        ui_locale = flask_babel.get_locale() or babel.Locale.parse("en")
        from_name: str = CURRENCIES.iso4217_to_name(
            from_iso4217, ui_locale.language
        )  # pyright: ignore[reportAssignmentType]
        to_name: str = CURRENCIES.iso4217_to_name(
            to_iso4217, ui_locale.language
        )  # pyright: ignore[reportAssignmentType]

        params: OnlineCurrenciesParams = {
            **online_params,
            "amount": amount,
            "from_iso4217": from_iso4217,
            "to_iso4217": to_iso4217,
            "from_name": from_name,
            "to_name": to_name,
        }

        return params


def _normalize_name(name: str):
    name = name.strip()
    name = name.lower().replace("-", " ")
    name = re.sub(" +", " ", name)
    return unicodedata.normalize("NFKD", name).lower()
