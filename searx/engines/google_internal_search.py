# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""This is the implementation of the google WEB engine using the google internal API used on the mobile UI.
This internal API offer results in
- JSON (_fmt:json)
- Protobuf (_fmt:pb)
- Protobuf compressed? (_fmt:pc)
- HTML (_fmt:html)
- Protobuf encoded in JSON (_fmt:jspb).

Some of this implementations are shared by other engines:
The implementation is shared by other engines:

- :ref:`google images internal engine`
- :ref:`google news internal engine`
- :ref:`google videos internal engine`

"""

from urllib.parse import urlencode
from json import loads, dumps
from datetime import datetime, timedelta
from dateutil.tz import tzoffset
from babel.dates import format_datetime
import babel
from searx.utils import html_to_text

# pylint: disable=unused-import
from searx.engines.google import (
    get_lang_info,
    detect_google_sorry,
    supported_languages_url,
    time_range_dict,
    filter_mapping,
    _fetch_supported_languages,
)

# pylint: enable=unused-import

# about
about = {
    "website": 'https://www.google.com',
    "wikidata_id": 'Q9366',
    "official_api_documentation": 'https://developers.google.com/custom-search/',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = None
paging = True
time_range_support = True
safesearch = True
send_accept_language_header = True

# configuration
include_image_results = True
include_twitter_results = False


def get_query_url_general(query, lang_info, query_params):
    return (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                **query_params,
            }
        )
    )


def get_query_url_images(query, lang_info, query_params):
    # https://www.google.de/search?q=corona&hl=de&lr=lang_de&start=0&tbs=qdr%3Ad&safe=medium
    return (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                'tbm': "isch",
                **query_params,
            }
        )
    )


def get_query_url_news(query, lang_info, query_params):
    return (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                'tbm': "nws",
                **query_params,
            }
        )
    )


CATEGORY_TO_GET_QUERY_URL = {
    'general': get_query_url_general,
    'images': get_query_url_images,
    'news': get_query_url_news,
}

CATEGORY_RESULT_COUNT_PER_PAGE = {
    'general': 10,
    'images': 100,
    'news': 10,
}


def request(query, params):
    """Google search request"""

    result_count_per_page = CATEGORY_RESULT_COUNT_PER_PAGE[categories[0]]  # pylint: disable=unsubscriptable-object

    offset = (params['pageno'] - 1) * result_count_per_page

    lang_info = get_lang_info(params, supported_languages, language_aliases, True)

    query_params = {
        **lang_info['params'],
        'ie': 'utf8',
        'oe': 'utf8',
        'start': offset,
        'num': result_count_per_page,
        'filter': '0',
        'asearch': 'arc',
        'async': 'use_ac:true,_fmt:json',
    }

    get_query_url = CATEGORY_TO_GET_QUERY_URL[categories[0]]  # pylint: disable=unsubscriptable-object

    # https://www.google.de/search?q=corona&hl=de&lr=lang_de&start=0&tbs=qdr%3Ad&safe=medium
    query_url = get_query_url(query, lang_info, query_params)

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = '*/*'

    return params


def parse_search_feature_proto(search_feature_proto):
    result_index = search_feature_proto["feature_metadata"]["logging_tree_ref_feature_metadata_extension"][
        "result_index"
    ]
    image_result_data = search_feature_proto["payload"]["image_result_data"]
    title = html_to_text(image_result_data["page_title"])
    content = html_to_text(image_result_data.get("snippet", ""))
    url = image_result_data["coupled_url"]
    img_src = image_result_data["url"]
    thumbnail_src = "https://encrypted-tbn0.gstatic.com/images?q=tbn:" + image_result_data["encrypted_docid"]
    img_format = f'{image_result_data["full_image_size"]["width"]} * {image_result_data["full_image_size"]["height"]}'

    iptc = image_result_data.get("iptc_info", {}).get("iptc", {})
    copyright_notice = iptc.get("copyright_notice")
    creator = iptc.get("creator")
    if isinstance(creator, list):
        creator = ", ".join(creator)
    if creator and copyright_notice and creator != copyright_notice:
        author = f'{creator} ; {copyright_notice}'
    else:
        author = creator
    return {
        "template": "images.html",
        "title": title,
        "content": content,
        "url": url,
        "img_src": img_src,
        "thumbnail_src": thumbnail_src,
        'img_format': img_format,
        "author": author,
        "result_index": result_index,
    }


class ParseResultGroupItem:
    """Parse result_group_search_feature_proto.search_feature_proto"""

    def __init__(self, locale):
        """Parse one tier 1 result"""
        self.locale = locale
        self.item_types = {
            "EXPLORE_UNIVERSAL_BLOCK": self.explore_universal_block,
            "HOST_CLUSTER": self.host_cluster,
            "NAVIGATIONAL_RESULT_GROUP": self.navigational_result_group,
            "VIDEO_RESULT": self.video_result,
            "VIDEO_UNIVERSAL_GROUP": self.video_universal_group,
            "WEB_RESULT": self.web_result,
            "WEB_ANSWERS_CARD_BLOCK": self.web_answers_card_block,
            "IMAGE_RESULT_GROUP": self.image_result_group,
            "TWITTER_RESULT_GROUP": self.twitter_result_group,
            "NEWS_WHOLEPAGE": self.news_wholepage,
            # WHOLEPAGE_PAGE_GROUP - found for keyword what is t in English language
            # EXPLORE_UNIVERSAL_BLOCK
            # TRAVEL_ANSWERS_RESULT
            # TOP_STORIES : news.html template
            # ONEBOX_BLOCK: for example, result of math forumla, weather ...
        }

    def explore_universal_block(self, item_to_parse):
        results = []
        for item in item_to_parse["explore_universal_unit_sfp_interface"]:
            explore_unit = item["explore_block_extension"]["payload"]["explore_unit"]
            if "lookup_key" in explore_unit:
                results.append(
                    {'suggestion': html_to_text(explore_unit["lookup_key"]["aquarium_query"]), 'result_index': -1}
                )
            elif "label" in explore_unit:
                results.append({'suggestion': html_to_text(explore_unit["label"]["text"]), 'result_index': -1})
        return results

    def host_cluster(self, item_to_parse):
        results = []
        for navigational_result in item_to_parse["results"]:
            result_index = navigational_result["web_result_inner"]["feature_metadata"][
                "logging_tree_ref_feature_metadata_extension"
            ]["result_index"]
            url = None
            title = None
            content = None

            for item in navigational_result["payload"]["sub_features"]["sub_feature"]:
                payload = item["search_feature_proto"]["payload"]
                if "primary_link" in payload:
                    primary_link = payload["primary_link"]
                    title = html_to_text(primary_link["title"])
                    url = primary_link["url"]
                if "snippet_text" in payload:
                    content = html_to_text(payload["snippet_text"])
            results.append({'url': url, 'title': title, 'content': content, 'result_index': result_index})
        # to do: parse additional results
        return results

    def navigational_result_group(self, item_to_parse):
        results = []
        navigational_result = item_to_parse["navigational_result"]
        result_index = navigational_result["navigational_result_inner"]["feature_metadata"][
            "logging_tree_ref_feature_metadata_extension"
        ]["result_index"]
        url = None
        title = None
        content = None

        for item in navigational_result["payload"]["sub_features"]["sub_feature"]:
            payload = item["search_feature_proto"]["payload"]
            if "primary_link" in payload:
                primary_link = payload["primary_link"]
                title = html_to_text(primary_link["title"])
                url = primary_link["url"]
            if "snippet_text" in payload:
                content = html_to_text(payload["snippet_text"])
        results.append({'url': url, 'title': title, 'content': content, 'result_index': result_index})

        for item in item_to_parse["megasitelinks"]["results"]:
            result_data = item["payload"]["result_data"]
            url = result_data["url"]
            title = html_to_text(result_data["result_title"])
            content = html_to_text(result_data["snippet"])
            result_index = item["feature_metadata"]["logging_tree_ref_feature_metadata_extension"]["result_index"]
            results.append({'url': url, 'title': title, 'content': content, 'result_index': result_index})

        return results

    def video_result(self, item_to_parse):
        result_index = item_to_parse["feature_metadata"]["logging_tree_ref_feature_metadata_extension"]["result_index"]
        url = None
        title = None

        for item in item_to_parse["payload"]["sub_features"]["sub_feature"]:
            payload = item["search_feature_proto"]["payload"]
            if "primary_link" in payload:
                primary_link = payload["primary_link"]
                title = html_to_text(primary_link["title"])
                url = primary_link["url"]

        return [{'url': url, 'title': title, 'result_index': result_index}]

    def video_universal_group(self, item_to_parse):
        results = []

        for item in item_to_parse["video_universal_group_element"]:
            video_result = item["video_result"]
            result_index = video_result["feature_metadata"]["logging_tree_ref_feature_metadata_extension"][
                "result_index"
            ]
            video_result_data = video_result["payload"]["video_result_data"]
            url = video_result_data["url"]
            title = html_to_text(video_result_data["title"])
            content = html_to_text(video_result_data["snippet"])
            results.append({'url': url, 'title': title, 'content': content, 'result_index': result_index})

        return results

    def web_result(self, item_to_parse):
        result_index = item_to_parse["web_result_inner"]["feature_metadata"][
            "logging_tree_ref_feature_metadata_extension"
        ]["result_index"]
        url = None
        title = None
        content = None

        for item in item_to_parse["payload"]["sub_features"]["sub_feature"]:
            payload = item["search_feature_proto"]["payload"]
            if "primary_link" in payload:
                primary_link = payload["primary_link"]
                title = html_to_text(primary_link["title"])
                url = primary_link["url"]
            if "snippet_text" in payload:
                content = html_to_text(payload["snippet_text"])

        return [{'url': url, 'title': title, 'content': content, 'result_index': result_index}]

    def web_answers_card_block(self, item_to_parse):
        results = []

        for item in item_to_parse["web_answers_card_block_elements"]:
            answer = None
            url = None
            for item_webanswers in item["webanswers_container"]["webanswers_container_elements"]:
                if (
                    "web_answers_result" in item_webanswers
                    and "text" in item_webanswers["web_answers_result"]["payload"]
                ):
                    answer = html_to_text(item_webanswers["web_answers_result"]["payload"]["text"])
                if "web_answers_standard_result" in item_webanswers:
                    primary_link = item_webanswers["web_answers_standard_result"]["payload"]["standard_result"][
                        "primary_link"
                    ]
                    url = primary_link["url"]

            results.append({'answer': answer, 'url': url, 'result_index': -1})

        return results

    def twitter_result_group(self, item_to_parse):
        results = []
        if not include_twitter_results:
            return results

        result_index = item_to_parse["twitter_carousel_header"]["feature_metadata"][
            "logging_tree_ref_feature_metadata_extension"
        ]["result_index"]
        for item in item_to_parse["twitter_cards"]:
            profile_payload = item["profile_link"]["payload"]["author"]
            results.append(
                {
                    "title": profile_payload["display_name"],
                    "url": profile_payload["profile_page_url"],
                    "result_index": result_index,
                }
            )

        return results

    def image_result_group(self, item_to_parse):
        results = []
        if not include_image_results:
            return results

        for item in item_to_parse["image_result_group_element"]:
            results.append(parse_search_feature_proto(item["image_result"]))
        return results

    def news_wholepage(self, item_to_parse):
        """Parse a news search result"""

        def iter_snippets():
            """Iterate over all the results, yield result_index, snippet to deal with nested structured"""
            result_index = 0
            for item in item_to_parse["element"]:
                if "news_singleton_result_group" in item:
                    payload = item["news_singleton_result_group"]["result"]["payload"]["liquid_item_data"]
                    yield result_index, payload["article"]["stream_simplified_snippet"]
                    result_index += 1
                    continue

                if "top_coverage" in item:
                    for element in item["top_coverage"]["element"]:
                        yield result_index, element["result"]["payload"]["liquid_item_data"]["article"][
                            "stream_simplified_snippet"
                        ]
                        result_index += 1
                    continue

                if "news_sports_hub_result_group" in item:
                    for element in item["news_sports_hub_result_group"]["element"]:
                        yield result_index, element["result"]["payload"]["liquid_item_data"]["article"][
                            "stream_simplified_snippet"
                        ]
                        result_index += 1
                    continue

                if "news_topic_hub_refinements_result_group" in item:
                    for ref_list in item["news_topic_hub_refinements_result_group"]["refinements"]["refinement_list"]:
                        for result in ref_list["results"]:
                            yield result_index, result["payload"]["liquid_item_data"]["article"][
                                "stream_simplified_snippet"
                            ]
                            result_index += 1
                    continue

                print("unknow news", item)

        results = []
        for result_index, snippet in iter_snippets():
            publishedDate = snippet["date"]["timestamp"]
            url = snippet["url"]["result_url"]
            title = html_to_text(snippet["title"]["text"])
            content = html_to_text(snippet["snippet"]["snippet"])
            img_src = snippet.get("thumbnail_info", {}).get("sffe_50k_thumbnail_url")
            results.append(
                {
                    'url': url,
                    'title': title,
                    'content': content,
                    'img_src': img_src,
                    'publishedDate': datetime.fromtimestamp(publishedDate),
                    "result_index": result_index,
                }
            )
        return results


class ParseResultItem:  # pylint: disable=too-few-public-methods
    """Parse result_search_feature_proto.search_feature_proto"""

    def __init__(self, locale):
        self.locale = locale
        self.item_types = {
            "LOCAL_TIME": self.local_time,
            "IMAGE_RESULT": self.image_result,
        }

    def local_time(self, item_to_parse):
        """Query like 'time in auckland' or 'time'
        Note: localized_location reveal the location of the server
        """
        seconds_utc = item_to_parse["payload"]["current_time"]["seconds_utc"]
        timezones_0 = item_to_parse["payload"]["target_location"]["timezones"][0]
        iana_timezone = timezones_0["iana_timezone"]
        localized_location = timezones_0["localized_location"]
        # parse timezone_abbrev_specific to create result_tz
        # timezone_abbrev_specific for India is "UTC+5:30" and for New York is "UTC−4"
        # the values for offsets are respectively ["5", "30", "0"] and ["-4": "0"]
        timezone_abbrev_specific = timezones_0["timezone_abbrev_specific"]
        offsets = timezone_abbrev_specific.replace("UTC", "").replace("GMT", "").replace("−", "-").split(":")
        offsets.append("0")
        result_tz = tzoffset(iana_timezone, timedelta(hours=int(offsets[0]), minutes=int(offsets[1])))
        result_dt = datetime.fromtimestamp(seconds_utc, tz=result_tz)
        result_dt_str = format_datetime(result_dt, 'long', tzinfo=result_tz, locale=self.locale)
        answer = f"{result_dt_str} ( {localized_location} )"
        return [{'answer': answer, 'result_index': -1}]

    def image_result(self, item_to_parse):
        return [parse_search_feature_proto(item_to_parse)]


def parse_web_results_list(json_data, locale):
    results = []

    tier_1_search_results = json_data["arcResponse"]["search_results"]["tier_1_search_results"]
    results_list = tier_1_search_results["result_list"]["item"]

    if "spell_suggestion" in tier_1_search_results:
        spell_suggestion = tier_1_search_results["spell_suggestion"]
        if "spell_column" in spell_suggestion:
            for spell_suggestion in tier_1_search_results["spell_suggestion"]["spell_column"]:
                for spell_link in spell_suggestion["spell_link"]:
                    results.append({'correction': spell_link["raw_corrected_query"], 'result_index': -1})
        elif "full_page" in spell_suggestion:
            results.append({'correction': spell_suggestion["full_page"]["raw_query"], 'result_index': -1})

    parseResultItem = ParseResultItem(locale)
    parseResultGroupItem = ParseResultGroupItem(locale)
    for item in results_list:
        if "result_group" in item:
            result_item = item["result_group"]
            result_item_extension = result_item["result_group_extension"]
        elif "result" in item:
            result_item = item["result"]
            result_item_extension = result_item["result_extension"]
        one_namespace_type = result_item_extension["one_namespace_type"]
        if one_namespace_type in parseResultGroupItem.item_types and "result_group_search_feature_proto" in result_item:
            search_feature_proto = result_item["result_group_search_feature_proto"]["search_feature_proto"]
            results = results + parseResultGroupItem.item_types[one_namespace_type](search_feature_proto)
        elif one_namespace_type in parseResultItem.item_types and "result_search_feature_proto" in result_item:
            search_feature_proto = result_item["result_search_feature_proto"]["search_feature_proto"]
            results = results + parseResultItem.item_types[one_namespace_type](search_feature_proto)
        elif "result_group_search_feature_proto" in result_item:
            print(dumps(one_namespace_type))

    return sorted(results, key=lambda d: d['result_index'])


def response(resp):
    """Get response from google's search request"""

    detect_google_sorry(resp)

    language = resp.search_params["language"]
    locale = 'en'
    try:
        locale = babel.Locale.parse(language, sep='-')
    except babel.core.UnknownLocaleError:
        pass

    # only the 2nd line has the JSON content
    response_2nd_line = resp.text.split("\n", 1)[1]
    json_data = loads(response_2nd_line)

    return parse_web_results_list(json_data, locale)
