# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine to search using the Brave (WEB) Search API.

.. _Brave Search API: https://api-dashboard.search.brave.com/api-reference/web/search/get

Configuration
=============

The engine has the following mandatory setting:

- :py:obj:`api_key`

Optional settings are:

- :py:obj:`results_per_page`
- :py:obj:`brave_category` (search, videos, images, news, goggles)

.. code:: yaml

  - name: braveapi
    engine: braveapi
    api_key: 'YOUR-API-KEY'  # required
    results_per_page: 20     # optional
    brave_category: search

The API supports paging and time filters.
"""

import typing as t

from urllib.parse import urlencode
from dateutil import parser
import datetime
from searx.weather import DateTime

from searx.exceptions import SearxEngineAPIException
from searx.result_types import EngineResults
from searx.utils import html_to_text

from searx import locales
from searx.enginelib.traits import EngineTraits

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

about = {
    "website": "https://api.search.brave.com/",
    "wikidata_id": None,
    "official_api_documentation": "https://api-dashboard.search.brave.com/api-reference/web/search/get",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

api_key: str = ""
"""API key for Brave Search API (required)."""

categories = ["general", "web"]
paging = True
safesearch = True
time_range_support = True

results_per_page: int = 20
"""Maximum number of results per page (default 20)."""

brave_category: t.Literal["search", "videos", "images", "news", "goggles"] = "search"
"""Brave Search API categories:
- ``search``: Common WEB search
- ``videos``: search for videos
- ``images``: search for images
- ``news``: search for news
- ``goggles``: Common WEB search with custom rules, requires a :py:obj:`Goggles` URL.
"""

Goggles: str = ""
"""This should be a URL ending in ``.goggle``"""

base_url = "https://api.search.brave.com/res/v1/web/search"
"""Base URL for the Brave Search API."""

time_range_map = {"day": "past_day", "week": "past_week", "month": "past_month", "year": "past_year"}
"""Mapping of SearXNG time ranges to Brave API time ranges."""


countries = ["AR", "AU", "AT", "BE", "BR", "CA", "CL", "DK", "FI", "FR", 
             "DE", "GR", "HK", "IN", "ID", "IT", "JP", "KR", "MY", "MX", 
             "NL", "NZ", "NO", "CN", "PL", "PT", "PH", "RU", "SA", "ZA", 
             "ES", "SE", "CH", "TW", "TR", "GB", "US"]

# Result filter based on category
result_filter_map = {
    "search": ["web", "news", "videos", "images", "infobox", "locations", 
                "discussions", "faq", "summarizer", "rich"],
    "videos": ["videos", "web"],
    "images": ["images", "web"],
    "news": ["news", "web"],
}


def init(_):
    """Initialize the engine."""
    if not api_key:
        raise SearxEngineAPIException("No API key provided")


def request(query: str, params: "OnlineParams") -> None:
    """Create the API request."""
    search_args: dict[str, str | int | None] = {
        "q": query,
        "count": results_per_page,
        "offset": (params["pageno"] - 1),
        "text_decorations": False,
    }

    if params["time_range"]:
        search_args["time_range"] = time_range_map.get(params["time_range"])

    if params["safesearch"]:
        search_args["safesearch"] = "strict"

    # Add language support
    eng_lang = locales.get_engine_locale(params["searxng_locale"], traits.custom.get("ui_lang", {}), "en-us")
    if eng_lang:
        # Format language codes: first part lowercase, second part uppercase (e.g., en-US)
        lang_parts = eng_lang.split("-")
        if len(lang_parts) >= 2:
            # search_lang: just the language code (e.g., "en")
            search_lang = lang_parts[0].lower()
            # ui_lang: language-country format with country uppercase (e.g., "en-US")
            ui_lang = f"{lang_parts[0].lower()}-{lang_parts[1].upper()}"
            search_args["search_lang"] = search_lang
            search_args["ui_lang"] = ui_lang
            if lang_parts[0].upper() in countries:
                search_args["country"] = lang_parts[0].upper()
            else:
                search_args["country"] = "ALL"
        else:
            search_args["search_lang"] = eng_lang.lower()
    else:
        search_args["search_lang"] = "en"

    # Add Goggles if specified
    if brave_category == "goggles" and Goggles:
        search_args["goggles"] = Goggles


    params["url"] = f"{base_url}?{urlencode(search_args)}"
    params["headers"]["X-Subscription-Token"] = api_key


def _extract_published_date(published_date_raw: str):
    """Extract and parse the published date from the API response.

    Args:
        published_date_raw: Raw date string from the API

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not published_date_raw:
        return None

    try:
        return parser.parse(published_date_raw)
    except parser.ParserError:
        return None

def _get_thumbnail(result: dict) -> str:
    """Extract thumbnail URL from a result."""
    thumbnail_obj = result.get("thumbnail")
    if thumbnail_obj and isinstance(thumbnail_obj, dict) and not thumbnail_obj.get("logo", False):
        return thumbnail_obj.get("src", "")
    return ""


def _add_web_result(res: EngineResults, result: dict) -> None:
    """Add a web search result based on subtype."""

    # Get subtype from the result
    subtype = result.get("subtype", "")

    # Match on subtype to determine how to handle the result
    match subtype:
        case "location":
            # For location subtype, call the location handler directly
            _add_location_result(res, result)
        case "video":
            # For video subtype, call the video handler directly
            _add_video_result(res, result)
        case "book" | "article":
            # For book and article subtypes, call the paper handler
            _add_paper_result(res, result)
        case _:
            # Default handling for regular web results and other subtypes
            res.add(
                res.types.MainResult(
                    url=result.get("url"),
                    title=html_to_text(result.get("title", "")),
                    content=html_to_text(result.get("description", "")),
                    publishedDate=_extract_published_date(result.get("age")),
                    thumbnail=_get_thumbnail(result),
                ),
            )


def _add_news_result(res: EngineResults, result: dict) -> None:
    """Add a news search result."""
    res.add(
        res.types.MainResult(
            url=result.get("url"),
            title=html_to_text(result.get("title", "")),
            content=html_to_text(result.get("description", "")),
            publishedDate=_extract_published_date(result.get("age")),
            thumbnail=_get_thumbnail(result),
        ),
    )

def _parse_duration(duration_str: str) -> int:
    """Parse duration string in HH:MM:SS or MM:SS format and return seconds."""
    if not duration_str:
        return 0
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError):
        return 0

def _add_video_result(res: EngineResults, result: dict) -> None:
    """Add a video search result with additional fields."""

    # Get video-specific data
    video_data = result.get("video", {})

    # Extract duration/length
    length = datetime.timedelta(seconds=_parse_duration(video_data.get("duration", "")))

    # Extract views count
    views_count = video_data.get("views", 0)
    views = str(views_count) if views_count else ""

    # Extract author/creator
    author = video_data.get("creator", "")
    if not author:
        video_author = video_data.get("author", {})
        if isinstance(video_author, dict):
            author = video_author.get("name", "")

    tags = video_data.get("tags", [])
    metadata = ", ".join(tags) if tags else ""

    thumbnail_obj = result.get("thumbnail")
    thumbnail = ""
    if thumbnail_obj and isinstance(thumbnail_obj, dict):
        thumbnail = thumbnail_obj.get("src", "")
    
    video_result = {
        "template": "videos.html",
        "url": result.get("url"),
        "title": html_to_text(result.get("title", "")),
        "content": html_to_text(result.get("description", "")),
        "publishedDate": _extract_published_date(result.get("age")),
        "thumbnail": thumbnail,
        "length": length,
        "views": views,
        "author": author,
        "metadata": metadata,
    }
    res.add(video_result)

def _add_image_result(res: EngineResults, result: dict) -> None:
    """Add an image search result."""
    res.add(
        res.types.MainResult(
            template="images.html",
            url=result.get("url"),
            title=html_to_text(result.get("title", "")),
            content=html_to_text(result.get("description", "")),
            img_src=result.get("url"),
            thumbnail=_get_thumbnail(result),
        ),
    )


def _add_infobox_result(res: EngineResults, result: dict) -> None:
    """Add an infobox result with detailed information from the Brave API."""
    title = html_to_text(result.get("title", ""))
    description = html_to_text(result.get("description", ""))
    long_desc = html_to_text(result.get("long_desc", ""))
    url = result.get("url", "")
    category = result.get("category", "")

    thumbnail_obj = result.get("thumbnail")
    img_src = ""
    if thumbnail_obj and isinstance(thumbnail_obj, dict):
        img_src = thumbnail_obj.get("src", "")

    urls = []
    seen_urls = set()

    def add_url(url_to_add, title_text):
        if url_to_add and url_to_add not in seen_urls:
            urls.append({"url": url_to_add, "title": title_text})
            seen_urls.add(url_to_add)

    if url:
        add_url(url, title or category or "More information")

    website_url = result.get("website_url")
    if website_url and website_url != url:
        add_url(website_url, "Website")

    found_in_urls = result.get("found_in_urls", [])
    for found_url in found_in_urls:
        if found_url:
            add_url(found_url, "Source")

    profiles = result.get("profiles", [])
    for profile in profiles:
        if isinstance(profile, dict) and profile.get("url"):
            add_url(profile["url"], profile.get("name", "Profile"))

    providers = result.get("providers", [])
    for provider in providers:
        if isinstance(provider, dict) and provider.get("url"):
            add_url(provider["url"], provider.get("name", "Provider"))

    movie_data = result.get("movie")
    if isinstance(movie_data, dict) and movie_data.get("url"):
        add_url(movie_data["url"], movie_data.get("name", "Movie"))

    attr_dict = {}

    # Handle API attributes first - they have priority
    api_attributes = result.get("attributes", [])
    if api_attributes and isinstance(api_attributes, list):
        for pair in api_attributes:
            if isinstance(pair, list) and len(pair) >= 2:
                name = html_to_text(str(pair[0]))
                value = html_to_text(str(pair[1]))
                if name and value and name.lower() != "generic":
                    attr_dict[name] = value

    # Add other attributes only if not already present from api_attributes
    if category and "Category" not in attr_dict:
        attr_dict["Category"] = category

    page_age = result.get("page_age")
    if page_age and "Date" not in attr_dict:
        attr_dict["Date"] = page_age

    distance_data = result.get("distance")
    if isinstance(distance_data, dict) and "Distance" not in attr_dict:
        distance_value = distance_data.get("value", "")
        distance_units = distance_data.get("units", "")
        if distance_value and distance_units:
            attr_dict["Distance"] = f"{distance_value} {distance_units}"

    ratings = result.get("ratings", [])
    if ratings and isinstance(ratings[0], dict) and "Rating" not in attr_dict:
        rating_data = ratings[0]
        rating_value = rating_data.get("ratingValue", "")
        best_rating = rating_data.get("bestRating", "")
        review_count = rating_data.get("reviewCount", "")
        if rating_value:
            rating_str = str(rating_value)
            if best_rating:
                rating_str += f"/{best_rating}"
            if review_count:
                rating_str += f" ({review_count} reviews)"
            attr_dict["Rating"] = rating_str

    if isinstance(movie_data, dict):
        if movie_data.get("release") and "Release" not in attr_dict:
            attr_dict["Release"] = movie_data["release"]
        if movie_data.get("duration") and "Duration" not in attr_dict:
            attr_dict["Duration"] = movie_data["duration"]

        directors = movie_data.get("directors", [])
        if directors and "Directors" not in attr_dict:
            director_names = []
            for director in directors:
                if isinstance(director, dict) and director.get("name"):
                    director_names.append(director["name"])
            if director_names:
                attr_dict["Directors"] = ", ".join(director_names)

        actors = movie_data.get("actors", [])
        if actors and "Actors" not in attr_dict:
            actor_names = []
            for actor in actors:
                if isinstance(actor, dict) and actor.get("name"):
                    actor_names.append(actor["name"])
            if actor_names:
                attr_dict["Actors"] = ", ".join(actor_names)

        genres = movie_data.get("genre", [])
        if genres and "Genres" not in attr_dict:
            attr_dict["Genres"] = ", ".join(genres)

    language = result.get("language")
    if language and "Language" not in attr_dict:
        attr_dict["Language"] = language

    subtype = result.get("subtype")
    if subtype and subtype != "generic" and subtype != "code" and "Type" not in attr_dict:
        attr_dict["Type"] = subtype

    profile = result.get("profile")
    if isinstance(profile, dict):
        if profile.get("name") and "Profile Name" not in attr_dict:
            attr_dict["Profile Name"] = profile["name"]
        if profile.get("long_name") and "Full Name" not in attr_dict:
            attr_dict["Full Name"] = profile["long_name"]

    #for subtype = code:
    content = None
    if subtype == "code":
        code_data = result.get("data", {})
        answer_data = code_data.get("answer", {})

        answer_text = answer_data.get("text", "")
        if answer_text:
            content = html_to_text(answer_text)
        else:
            content = long_desc or description

        answer_author = answer_data.get("author", "")
        if answer_author:
            attr_dict["Author"] = answer_author

        upvotes = answer_data.get("upvoteCount")
        if upvotes:
            attr_dict["Upvotes"] = str(upvotes)
    else:
        content = long_desc or description

    attributes = [{"label": k, "value": v} for k, v in attr_dict.items()]

    infobox_result = res.types.LegacyResult({
        "infobox": title,
        "id": url,
        "title": title,
        "content": content,
        "img_src": img_src,
        "urls": urls,
        "attributes": attributes,
        "category": category,
    })

    res.add(infobox_result)

def _add_paper_result(res: EngineResults, result: dict) -> None:
    """Add a paper/book/article result based on subtype."""

    subtype = result.get("subtype", "")

    # Get the book or article data
    if subtype == "book":
        paper_data = result.get("book", {})
    else:  # article
        paper_data = result.get("article", {})

    title = html_to_text(paper_data.get("title", result.get("title", "")))
    url = result.get("url", "")

    content = html_to_text(result.get("description", ""))

     # Date of publication
    date_str = paper_data.get("date", result.get("page_age"))
    date_of_publication = None
    if date_str:
        try:
        # Try parsing date in format "Aug 22, 2023"
            date_of_publication = DateTime(datetime.strptime(date_str, "%b %d, %Y"))
        except:
            date_of_publication = None

    # Authors
    authors = []
    author_list = paper_data.get("author", [])
    if isinstance(author_list, list):
        for author in author_list:
            if isinstance(author, dict) and author.get("name"):
                authors.append(html_to_text(author["name"]))

    # Publisher
    publisher_data = paper_data.get("publisher", {})
    publisher = html_to_text(publisher_data.get("name", "")) if isinstance(publisher_data, dict) else ""

    # Journal
    journal = ""
    if subtype == "article" and isinstance(publisher_data, dict):
        journal = html_to_text(publisher_data.get("name", ""))

    # Pages
    pages = paper_data.get("pages", "")
    if isinstance(pages, int):
        pages = str(pages)

    # Type
    paper_type = "book" if subtype == "book" else "article"

    # Thumbnail
    thumbnail_obj = paper_data.get("thumbnail") or result.get("thumbnail")
    thumbnail = ""
    if thumbnail_obj and isinstance(thumbnail_obj, dict):
        thumbnail = thumbnail_obj.get("src", "")

    tags = []

    # price information to tags
    price_data = paper_data.get("price", {})
    if isinstance(price_data, dict):
        price = price_data.get("price", "")
        currency = price_data.get("priceCurrency", "")
        if price:
            tags.append(f"{price} {currency}")

    # Add rating information
    rating_data = paper_data.get("rating", {})
    if isinstance(rating_data, dict):
        rating_value = rating_data.get("ratingValue", "")
        best_rating = rating_data.get("bestRating", "")
        review_count = rating_data.get("reviewCount", "")
        if rating_value:
            rating_str = str(rating_value)
            if best_rating:
                rating_str += f"/{best_rating}"
            if review_count:
                rating_str += f" ({review_count} reviews)"
            tags.append(rating_str)

    paper_result = {
        "template": "paper.html",
        "title": title,
        "url": url,
        "content": content,
        "date_of_publication": date_of_publication,
        "authors": authors,
        "journal": journal,
        "pages": pages,
        "type": paper_type,
        "thumbnail": thumbnail,
        "tags": tags,
    }

    res.add(paper_result)


def _add_location_result(res: EngineResults, result: dict) -> None:
    """Add a location search result."""

    if "location" in result:
        location_data = result["location"]
    else:
        location_data = result

    # Get coordinates
    coordinates = location_data.get("coordinates", [])
    latitude = None
    longitude = None
    if isinstance(coordinates, list) and len(coordinates) >= 2:
        latitude = coordinates[0]
        longitude = coordinates[1]

    # Parse address - simplified: put everything in road (streetAddress)
    postal_address = location_data.get("postal_address", {})
    display_address = postal_address.get("displayAddress", "")

    address = {
        "name": "",
        "road": display_address,
        "house_number": "",
        "locality": "",
        "postcode": "",
        "country": ""
    }

    thumbnail_obj = location_data.get("thumbnail")
    thumbnail = ""
    if thumbnail_obj and isinstance(thumbnail_obj, dict):
        thumbnail = thumbnail_obj.get("src", "")

    title = html_to_text(location_data.get("title", ""))
    if not title:
        title = html_to_text(result.get("title", ""))

    url = location_data.get("url", "")
    if not url:
        url = result.get("url", "")

    data = []

    # Add contact information
    contact = location_data.get("contact", {})
    telephone = contact.get("telephone", "")
    if telephone:
        data.append({"label": "Phone: ", "value": telephone})

    price_range = location_data.get("price_range", "")
    if price_range:
        data.append({"label": "Price: ", "value": price_range})

    # Add rating
    rating = location_data.get("rating", {})
    if isinstance(rating, dict):
        rating_value = rating.get("ratingValue", "")
        best_rating = rating.get("bestRating", "")
        review_count = rating.get("reviewCount", "")
        if rating_value:
            rating_str = str(rating_value)
            if best_rating:
                rating_str += f"/{best_rating}"
            if review_count:
                rating_str += f" ({review_count} reviews)"
            data.append({"label": "Rating: ", "value": rating_str})

    serves_cuisine = location_data.get("serves_cuisine", [])
    if serves_cuisine:
        data.append({"label": "Cuisine: ", "value": ", ".join(serves_cuisine)})

    links = []
    if url:
        links.append({"label": "Website", "url_label": url})

    location_result = {
        "template": "map.html",
        "url": url,
        "title": title,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "thumbnail": thumbnail,
        "data": data,
        "links": links,
        "priority": "high",
    }

    res.add(location_result)


def _add_discussion_result(res: EngineResults, result: dict) -> None:
    """Add a discussion search result."""
    res.add(
        res.types.MainResult(
            template="default.html",
            url=result.get("url"),
            title=html_to_text(result.get("title", "")),
            content=html_to_text(result.get("description", "")),
            publishedDate=_extract_published_date(result.get("age")),
        ),
    )


def _add_faq_result(res: EngineResults, result: dict) -> None:
    """Add an FAQ search result."""
    question = html_to_text(result.get("question", ""))
    answer = html_to_text(result.get("answer", ""))
    res.add(
        res.types.MainResult(
            template="default.html",
            url=result.get("url"),
            title=question,
            content=answer,
        ),
    )



def response(resp: "SXNG_Response") -> EngineResults:
    """Process the API response and return results."""
    res = EngineResults()
    data = resp.json()

    web_section = data.get("web")
    if web_section and web_section.get("results"):
        for result in web_section["results"]:
            _add_web_result(res, result)

    news_section = data.get("news")
    if news_section and news_section.get("results"):
        for result in news_section["results"]:
            _add_news_result(res, result)

    videos_section = data.get("videos")
    if videos_section and videos_section.get("results"):
        for result in videos_section["results"]:
            _add_video_result(res, result)

    images_section = data.get("images")
    if images_section and images_section.get("results"):
        for result in images_section["results"]:
            _add_image_result(res, result)

    infobox_section = data.get("infobox")
    if infobox_section and infobox_section.get("results"):
        for result in infobox_section["results"]:
            _add_infobox_result(res, result)

    locations_section = data.get("locations")
    if locations_section and locations_section.get("results"):
        for result in locations_section["results"]:
            _add_location_result(res, result)

    discussions_section = data.get("discussions")
    if discussions_section and discussions_section.get("results"):
        for result in discussions_section["results"]:
            _add_discussion_result(res, result)

    faq_section = data.get("faq")
    if faq_section and faq_section.get("results"):
        for result in faq_section["results"]:
            _add_faq_result(res, result)

    return res

