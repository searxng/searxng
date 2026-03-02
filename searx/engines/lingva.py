# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Lingva Translate`_ is an alternative front-end for Google Translate,
serving as a free and open source translator with over a hundred
languages available.

.. _Lingva Translate: https://github.com/thedaviddelta/lingva-translate
"""

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors.online_dictionary import OnlineDictParams

about: dict[str, t.Any] = {
    "website": "https://github.com/thedaviddelta/lingva-translate",
    "wikidata_id": None,
    "official_api_documentation": "https://github.com/thedaviddelta/lingva-translate#public-apis",
    "use_official_api": True,
    "require_api_key": False,
    "results": "JSON",
}

categories: list[str] = ["general", "translate"]
engine_type = "online_dictionary"

base_url = "https://lingva.ml"


def request(_query: str, params: "OnlineDictParams") -> None:
    from_lang = params["from_lang"][1]
    to_lang = params["to_lang"][1]
    query = params["query"]

    params["url"] = f"{base_url}/api/v1/{from_lang}/{to_lang}/{query}"


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_resp = resp.json()

    params: "OnlineDictParams" = resp.search_params  # type: ignore[assignment]
    from_lang = params["from_lang"][1]
    to_lang = params["to_lang"][1]
    query = params["query"]

    translation = json_resp.get("translation")
    if not translation:
        return res

    info: dict[str, t.Any] | None = json_resp.get("info")

    from_to_prefix = f"{from_lang}-{to_lang} "

    translations: list[EngineResults.types.Translations.Item] = []

    if info:
        if "typo" in info:
            res.add(res.types.LegacyResult(suggestion=from_to_prefix + info["typo"]))

        for definition in info.get("definitions", []):
            for item in definition.get("list", []):
                for synonym in item.get("synonyms", []):
                    res.add(res.types.LegacyResult(suggestion=from_to_prefix + synonym))

                translations.append(
                    EngineResults.types.Translations.Item(
                        text=translation,
                        definitions=[item["definition"]] if item.get("definition") else [],
                        examples=[item["example"]] if item.get("example") else [],
                        synonyms=item.get("synonyms", []),
                    )
                )

        for extra_translation in info.get("extraTranslations", []):
            for word in extra_translation.get("list", []):
                translations.append(
                    EngineResults.types.Translations.Item(
                        text=word["word"],
                        definitions=word.get("meanings", []),
                    )
                )

    if not translations:
        translations.append(EngineResults.types.Translations.Item(text=translation))

    res.add(
        res.types.Translations(
            translations=translations,
            url=f"{base_url}/{from_lang}/{to_lang}/{query}",
        )
    )

    return res
