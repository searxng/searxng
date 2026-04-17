# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared provider integration for Google API engines."""

from __future__ import annotations

import typing as t
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse

from dateutil import parser as date_parser

from searx.exceptions import (
    SearxEngineAPIException,
    SearxEngineTooManyRequestsException,
)
from searx.locales import get_locale
from searx.utils import get_embeded_stream_url

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

GOOGLE_API_PROVIDERS = {"serpbase", "serper"}
GOOGLE_API_SEARCH_TYPES = {"search", "images", "news", "videos"}

TIME_RANGE_DICT = {"day": "d", "week": "w", "month": "m", "year": "y"}
SAFESEARCH_DICT = {0: "off", 1: "active", 2: "active"}
SERPBASE_POSTED_RE = re.compile(r"Posted:\s*(.+)$")
SERPBASE_META_SEPARATOR_RE = re.compile(r"\s+[^\w\s]{1,3}\s+")

SERPBASE_ENDPOINTS = {
    "search": "https://api.serpbase.dev/google/search",
    "images": "https://api.serpbase.dev/google/images",
    "news": "https://api.serpbase.dev/google/news",
    "videos": "https://api.serpbase.dev/google/videos",
}

SERPER_ENDPOINTS = {
    "search": "https://google.serper.dev/search",
    "images": "https://google.serper.dev/images",
    "news": "https://google.serper.dev/news",
    "videos": "https://google.serper.dev/videos",
}


def validate_google_api_config(provider: str, api_key: str) -> None:
    if provider not in GOOGLE_API_PROVIDERS:
        raise SearxEngineAPIException(f"Unsupported Google API provider: {provider}")
    if not api_key:
        raise SearxEngineAPIException("No API key provided")


def get_google_api_locale(searxng_locale: str) -> tuple[str, str]:
    locale = get_locale(searxng_locale)
    if locale is None:
        return "en", "us"

    language = locale.language or "en"
    if locale.script and language == "zh":
        language = f"{language}-{locale.script}"

    country = locale.territory or "US"
    return language, country.lower()


def request_google_api(
    query: str,
    params: "OnlineParams",
    *,
    provider: str,
    api_key: str,
    search_type: str,
) -> None:
    validate_google_api_config(provider, api_key)
    if search_type not in GOOGLE_API_SEARCH_TYPES:
        raise SearxEngineAPIException(
            f"Unsupported Google API search type: {search_type}"
        )

    hl, gl = get_google_api_locale(params["searxng_locale"])
    payload: dict[str, t.Any] = {
        "q": query,
        "hl": hl,
        "gl": gl,
        "page": params["pageno"],
    }

    params["method"] = "POST"
    params["headers"]["Content-Type"] = "application/json"

    if provider == "serpbase":
        params["headers"]["X-API-Key"] = api_key
        params["url"] = SERPBASE_ENDPOINTS[search_type]
    else:
        time_range = params.get("time_range")
        if time_range in TIME_RANGE_DICT:
            payload["tbs"] = f"qdr:{TIME_RANGE_DICT[time_range]}"

        if "safesearch" in params:
            payload["safe"] = SAFESEARCH_DICT.get(params["safesearch"], "off")

        params["headers"]["X-API-KEY"] = api_key
        params["url"] = SERPER_ENDPOINTS[search_type]

    params["json"] = payload


def response_google_api(
    resp: "SXNG_Response", *, provider: str, search_type: str
) -> list[dict[str, t.Any]]:
    if search_type not in GOOGLE_API_SEARCH_TYPES:
        raise SearxEngineAPIException(
            f"Unsupported Google API search type: {search_type}"
        )

    data: dict[str, t.Any] = resp.json()
    if provider == "serpbase":
        _raise_serpbase_error(data)
        normalized = _normalize_serpbase(data, search_type)
    elif provider == "serper":
        _raise_serper_error(data, search_type)
        normalized = _normalize_serper(data, search_type)
    else:
        raise SearxEngineAPIException(f"Unsupported Google API provider: {provider}")

    return _to_searx_results(normalized, search_type)


def _raise_serpbase_error(data: dict[str, t.Any]) -> None:
    status = data.get("status")
    if status == 0:
        return

    message = data.get("error") or f"SerpBase API error: status={status}"
    if status == 1029:
        raise SearxEngineTooManyRequestsException(message=message)
    raise SearxEngineAPIException(message)


def _raise_serper_error(data: dict[str, t.Any], search_type: str) -> None:
    result_key = "organic" if search_type == "search" else search_type
    if data.get("message") and not data.get(result_key):
        raise SearxEngineAPIException(data["message"])


def _normalize_serpbase(data: dict[str, t.Any], search_type: str) -> dict[str, t.Any]:
    items_key = "organic" if search_type == "search" else search_type
    return {
        "items": [
            _normalize_item(item, search_type, "serpbase")
            for item in data.get(items_key, [])
        ],
        "suggestions": list(data.get("related_searches", [])),
    }


def _normalize_serper(data: dict[str, t.Any], search_type: str) -> dict[str, t.Any]:
    items_key = "organic" if search_type == "search" else search_type
    suggestions: list[str] = []
    for suggestion in data.get("relatedSearches", []):
        if isinstance(suggestion, dict):
            query = suggestion.get("query")
        else:
            query = suggestion
        if query:
            suggestions.append(query)

    return {
        "items": [
            _normalize_item(item, search_type, "serper")
            for item in data.get(items_key, [])
        ],
        "suggestions": suggestions,
    }


def _normalize_item(
    item: dict[str, t.Any], search_type: str, provider: str
) -> dict[str, t.Any]:
    if search_type == "search":
        return {
            "url": item.get("link"),
            "title": item.get("title"),
            "content": item.get("snippet", ""),
            "thumbnail": item.get("icon"),
        }

    if search_type == "images":
        image_url = item.get("imageUrl") or item.get("image_url") or item.get("img_src")
        thumbnail_url = (
            item.get("thumbnailUrl") or item.get("thumbnail_url") or image_url
        )
        resolution = None
        width = item.get("imageWidth") or item.get("width")
        height = item.get("imageHeight") or item.get("height")
        if width and height:
            resolution = f"{width} x {height}"

        return {
            "url": item.get("link"),
            "title": item.get("title"),
            "content": item.get("snippet", item.get("domain", "")),
            "source": item.get("source", item.get("domain", "")),
            "img_src": image_url,
            "thumbnail_src": thumbnail_url,
            "resolution": resolution,
            "template": "images.html" if image_url or thumbnail_url else None,
        }

    if search_type == "news":
        meta = (
            _parse_serpbase_source_meta(item.get("source"))
            if provider == "serpbase"
            else {}
        )
        snippet = item.get("snippet", item.get("source", ""))
        published_raw = (
            item.get("date") or item.get("time") or meta.get("published_raw")
        )
        published_date = _parse_published_date(published_raw)
        return {
            "url": item.get("link"),
            "title": item.get("title"),
            "content": snippet,
            "thumbnail": item.get("imageUrl") or item.get("thumbnail_url"),
            "author": (
                (
                    _parse_serpbase_news_author(snippet, item.get("time"))
                    or meta.get("author")
                )
                if provider == "serpbase"
                else item.get("source")
            ),
            "publishedDate": published_date,
        }

    iframe_src = (
        get_embeded_stream_url(item.get("link", "")) if item.get("link") else None
    ) or _get_video_embed_url(item.get("link"))
    meta = _parse_serpbase_video_meta(item) if provider == "serpbase" else {}
    author = item.get("channel") or meta.get("author")
    if provider != "serpbase" and not author:
        author = item.get("source")
    published_date = _parse_published_date(
        item.get("date") or item.get("time") or meta.get("published_raw")
    )
    thumbnail = (
        item.get("imageUrl")
        or item.get("thumbnail_url")
        or _get_video_thumbnail(item.get("link"))
    )

    return {
        "url": item.get("link"),
        "title": item.get("title"),
        "content": item.get("snippet") or meta.get("description") or "",
        "thumbnail": thumbnail,
        "author": author,
        "length": item.get("duration") or meta.get("duration"),
        "publishedDate": published_date,
        "iframe_src": iframe_src,
        "template": "videos.html",
    }


def _to_searx_results(
    normalized: dict[str, t.Any], search_type: str
) -> list[dict[str, t.Any]]:
    results: list[dict[str, t.Any]] = []
    for item in normalized["items"]:
        if not item.get("url") or not item.get("title"):
            continue
        if search_type == "images" and not item.get("template"):
            item.pop("template", None)
            item.pop("img_src", None)
            item.pop("thumbnail_src", None)
        results.append(item)

    if search_type == "search":
        for suggestion in normalized["suggestions"]:
            results.append({"suggestion": suggestion})

    return results


def _parse_published_date(value: t.Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None


def _join_nonempty(*parts: t.Any) -> str | None:
    values = [part for part in parts if isinstance(part, str) and part]
    return " | ".join(values) if values else None


def _parse_serpbase_source_meta(value: t.Any) -> dict[str, str]:
    if not isinstance(value, str) or not value.strip():
        return {}

    raw = value.strip()
    posted_match = SERPBASE_POSTED_RE.search(raw)
    published_raw = posted_match.group(1).strip() if posted_match else ""
    duration = ""
    author = raw

    if raw.startswith("Duration:"):
        duration_part = raw[len("Duration:") :]
        if posted_match:
            duration_part = duration_part[: posted_match.start() - len("Duration:")]
        duration = duration_part.strip(" -|")
        if duration == "Posted:" or duration.startswith("Posted:"):
            duration = ""
        author = ""
    elif posted_match:
        author = raw[: posted_match.start()].strip(" -|")

    if not author or author == raw:
        author = ""

    description_parts = [part for part in [author, duration, published_raw] if part]
    description = " | ".join(description_parts)
    if not description and raw.startswith("Duration:"):
        description = ""
    return {
        "author": author,
        "duration": duration,
        "published_raw": published_raw,
        "description": description,
    }


def _parse_serpbase_video_meta(item: dict[str, t.Any]) -> dict[str, str]:
    raw = item.get("source")
    if not isinstance(raw, str) or not raw.strip():
        return {}

    raw = raw.strip()
    posted_match = SERPBASE_POSTED_RE.search(raw)
    published_raw = (
        (item.get("time") or "").strip() if isinstance(item.get("time"), str) else ""
    )
    if not published_raw and posted_match:
        published_raw = posted_match.group(1).strip()

    duration = item.get("duration") if isinstance(item.get("duration"), str) else ""
    if not duration and raw.startswith("Duration:"):
        duration_part = raw[len("Duration:") :]
        if posted_match:
            duration_part = duration_part[: posted_match.start() - len("Duration:")]
        duration = duration_part.strip(" -|")
        if duration == "Posted:" or duration.startswith("Posted:"):
            duration = ""

    if raw.startswith("Duration:"):
        return {
            "author": "",
            "duration": duration,
            "published_raw": published_raw,
            "description": "",
        }

    if posted_match:
        author = raw[: posted_match.start()].strip(" -|")
        return {
            "author": author,
            "duration": duration,
            "published_raw": published_raw,
            "description": "",
        }

    if len(raw.split()) <= 4:
        return {
            "author": raw,
            "duration": duration,
            "published_raw": published_raw,
            "description": "",
        }

    return {
        "author": "",
        "duration": duration,
        "published_raw": published_raw,
        "description": raw,
    }


def _parse_serpbase_news_author(snippet: t.Any, relative_time: t.Any) -> str | None:
    if not isinstance(snippet, str) or not snippet.strip():
        return None
    if not isinstance(relative_time, str) or not relative_time.strip():
        return None

    parts = [
        part.strip()
        for part in SERPBASE_META_SEPARATOR_RE.split(snippet.strip())
        if part.strip()
    ]
    if len(parts) == 2 and parts[1] == relative_time.strip():
        return parts[0]
    return None


def _get_video_thumbnail(url: t.Any) -> str | None:
    video_id = _get_youtube_video_id(url)
    if not video_id:
        return None
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def _get_video_embed_url(url: t.Any) -> str | None:
    video_id = _get_youtube_video_id(url)
    if not video_id:
        return None
    return f"https://www.youtube-nocookie.com/embed/{video_id}"


def _get_youtube_video_id(url: t.Any) -> str | None:
    if not isinstance(url, str) or not url:
        return None

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith("youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]
    if host == "youtu.be":
        return parsed.path.strip("/") or None
    return None
