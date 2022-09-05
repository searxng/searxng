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
categories = ['general', 'web']
paging = True
time_range_support = True
safesearch = True
send_accept_language_header = True


def request(query, params):
    """Google search request"""

    offset = (params['pageno'] - 1) * 10

    lang_info = get_lang_info(params, supported_languages, language_aliases, True)

    # https://www.google.de/search?q=corona&hl=de&lr=lang_de&start=0&tbs=qdr%3Ad&safe=medium
    query_url = (
        'https://'
        + lang_info['subdomain']
        + '/search'
        + "?"
        + urlencode(
            {
                'q': query,
                **lang_info['params'],
                'ie': "utf8",
                'oe': "utf8",
                'start': offset,
                'filter': '0',
                'asearch': 'arc',
                'async': 'use_ac:true,_fmt:json',
            }
        )
    )

    if params['time_range'] in time_range_dict:
        query_url += '&' + urlencode({'tbs': 'qdr:' + time_range_dict[params['time_range']]})
    if params['safesearch']:
        query_url += '&' + urlencode({'safe': filter_mapping[params['safesearch']]})
    params['url'] = query_url

    params['headers'].update(lang_info['headers'])
    params['headers']['Accept'] = '*/*'

    return params


class ParseItem:
    """Parse one tier 1 result"""

    def __init__(self):
        self.item_types = {
            "EXPLORE_UNIVERSAL_BLOCK": self.explore_universal_block,
            "HOST_CLUSTER": self.host_cluster,
            "NAVIGATIONAL_RESULT_GROUP": self.navigational_result_group,
            "VIDEO_RESULT": self.video_result,
            "VIDEO_UNIVERSAL_GROUP": self.video_universal_group,
            "WEB_RESULT": self.web_result,
            "WEB_ANSWERS_CARD_BLOCK": self.web_answers_card_block,
            # WHOLEPAGE_PAGE_GROUP - found for keyword what is t in English language
            # IMAGE_RESULT_GROUP
            # EXPLORE_UNIVERSAL_BLOCK
            # TWITTER_RESULT_GROUP
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
                results.append({'suggestion': html_to_text(explore_unit["lookup_key"]["aquarium_query"]), 'result_index': -1})
            elif "label":
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
            title = None
            for item_webanswers in item["webanswers_container"]["webanswers_container_elements"]:
                if "web_answers_result" in item_webanswers and "text" in item_webanswers["web_answers_result"]["payload"]:
                    answer = html_to_text(item_webanswers["web_answers_result"]["payload"]["text"])
                if "web_answers_standard_result" in item_webanswers:
                    primary_link = item_webanswers["web_answers_standard_result"]["payload"]["standard_result"]["primary_link"]
                    url = primary_link["url"]

            results.append({'answer': answer, 'url': url, 'result_index': -1})

        return(results)

def parse_web_results_list(json_data):
    results = []

    tier_1_search_results = json_data["arcResponse"]["search_results"]["tier_1_search_results"]
    results_list = tier_1_search_results["result_list"]["item"]

    if "spell_suggestion" in tier_1_search_results:
        print(tier_1_search_results["spell_suggestion"])
        spell_suggestion = tier_1_search_results["spell_suggestion"]
        if "spell_column" in spell_suggestion:
            for spell_suggestion in tier_1_search_results["spell_suggestion"]["spell_column"]:
                for spell_link in spell_suggestion["spell_link"]:
                    results.append({'correction': spell_link["raw_corrected_query"], 'result_index': -1})
        elif "full_page" in spell_suggestion:
            results.append({'correction': spell_suggestion["full_page"]["raw_query"], 'result_index': -1})

    parse_item = ParseItem()
    for item in results_list:
        if "result_group" in item:
            result_item = item["result_group"]
            result_item_extension = result_item["result_group_extension"]
        elif "result" in item:
            result_item = item["result"]
            result_item_extension = result_item["result_extension"]
        one_namespace_type = result_item_extension["one_namespace_type"]
        if one_namespace_type in parse_item.item_types and "result_group_search_feature_proto" in result_item:
            search_feature_proto = result_item["result_group_search_feature_proto"]["search_feature_proto"]
            results = results + parse_item.item_types[one_namespace_type](search_feature_proto)
        elif "result_group_search_feature_proto" not in result_item:
            print(dumps(json_data["arcResponse"]))

    return sorted(results, key=lambda d: d['result_index'])


def response(resp):
    """Get response from google's search request"""

    detect_google_sorry(resp)

    # only the 2nd line has the JSON content
    response_2nd_line = resp.text.split("\n", 1)[1]
    json_data = loads(response_2nd_line)
    return parse_web_results_list(json_data)
