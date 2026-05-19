# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=invalid-name
"""Swisscows images"""

import json

import random
import base64
import codecs
import hashlib

from urllib.parse import urlencode

import typing as t

from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams


about = {
    "website": "https://swisscows.com",
    "wikidata_id": "Q22937452",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}


categories = ["images"]
paging = True
results_per_page = 50

base_url = "https://api.swisscows.com"

CAESAR_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NONCE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"


def generate_nonce(length: int = 32) -> str:
    """
    Generate a random char sequence with the given length.
    """
    return "".join([random.choice(NONCE_ALPHABET) for _ in range(length)])


def caesar_shift_with_switch_case(s: str, offset: int = 13) -> str:
    """
    Caesar shift by :py:obj:`offset` that additionally inverts the casing of all letters
    (i.e. from lowercase to uppercase and vice versa).
    """
    out = ""
    for c in s:
        if c.upper() in CAESAR_ALPHABET:
            alphabet_index = ord(c.upper()) - ord("A")
            shifted = CAESAR_ALPHABET[(alphabet_index + offset) % len(CAESAR_ALPHABET)]
            case_switched = shifted.lower() if c.isupper() else shifted.upper()
            out += case_switched
        else:
            out += c
    return out


def sha256_hash_b64_url(s: str) -> str:
    """
    Calculate the SHA256 hash and base64 URL-encodes it.
    """
    hasher = hashlib.sha256()
    hasher.update(s.encode())
    hashed_bytes = hasher.digest()

    # hashlib generates a byte digest, but since we need to convert it to base64, we
    # need to do that by hand
    hash_base64 = codecs.encode(hashed_bytes, "base64").decode("utf-8").rstrip('\n')

    hash_base64_url_encoded = hash_base64.replace("=", "").replace("+", '-').replace("/", '_')
    return hash_base64_url_encoded


def generate_nonce_and_signature(url_path: str) -> tuple[str, str]:
    """
    Generate "X-Request-Nonce" and "X-Request-Signature" which are required for accessing
    Swisscows images (reverse engineered from their official website).
    """
    nonce = generate_nonce()
    nonce_shifted = caesar_shift_with_switch_case(nonce, 13)

    signature = sha256_hash_b64_url(url_path + nonce_shifted)
    return (nonce, signature)


def request(query: str, params: "OnlineParams") -> None:
    # engine only supports 2 pages
    if params["pageno"] > 2:
        params["url"] = None
        return

    # the keys have to be sorted in alphabetic order,
    # otherwise the generated signature won't be accepted!
    args = {
        "itemsCount": results_per_page,
        "locale": "en-US",
        "offset": (params["pageno"] - 1) * results_per_page,
        "query": query,
        "spellcheck": True,
    }
    url_path = f"/v5/images/search?{urlencode(args)}"
    nonce, signature = generate_nonce_and_signature(url_path)

    params["headers"].update(
        {
            "X-Request-Nonce": nonce,
            "X-Request-Signature": signature,
        }
    )
    params["url"] = base_url + url_path


def response(resp: "SXNG_Response"):
    res = EngineResults()

    payload = resp.json()["payload"].split(".")[1]
    decoded = base64.urlsafe_b64decode(payload + '=' * (4 - len(payload) % 4))
    json_data = json.loads(decoded.decode())

    for result in json_data["items"]:
        res.add(
            res.types.LegacyResult(
                {
                    "template": "images.html",
                    "url": result["url"],
                    "thumbnail_src": result["thumbnail"]["url"],
                    "img_src": result["contentUrl"],
                    "title": result["name"],
                }
            )
        )

    return res
