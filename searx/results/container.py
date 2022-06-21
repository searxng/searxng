# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""ResultContainer
"""

from collections import defaultdict
from operator import itemgetter
from threading import RLock
from typing import List, Set
from urllib.parse import urlparse

from searx import logger
from searx.engines import engines
from searx.metrics import histogram_observe, counter_add, count_error

from .core import (
    WHITESPACE_REGEX,
    Timing,
    UnresponsiveEngine,
    result_content_len,
    result_score,
    compare_urls,
)

from .infobox import Infoboxes, merge_two_infoboxes, is_infobox
from .suggestion import Suggestions, is_suggestion
from .answer import Answers, is_answer
from .correction import Corrections, is_correction


def is_number_of_results(result):
    """Returns ``True`` if result type is ``number_of_results``, otherwise
    ``False``"""
    return 'number_of_results' in result


def is_engine_data(result):
    """Returns ``True`` if result type is :ref:`engine_data`, otherwise ``False``"""
    return 'engine_data' in result


def is_standard_result(result):
    """Returns ``True`` if result type is a :ref:`standard result <standard
    result>`, otherwise ``False``"""
    return 'url' in result


class ResultContainer:
    """A container to organize the result items and the various result types.  New
    results can be added by :py:obj:`ResultContainer.extend`.

    To be clear, a result-type is not a special python data-type, a result is
    always a python dicticonary.  The result-type is determined by the presence
    of one of the following keys (in that order, first match wins)

    1. suggestion: :py:obj:`.suggestion`
    2. answer: :py:obj:`.answer`
    3. correction: :py:obj:`.correction`
    4. infobox: :py:obj:`.infobox`
    5. number_of_results: Number of results origin engine has.

       .. code:: python

          results.append({
              'number_of_results' : int,
          })

    6. engine_data: used to pass :ref:`engine_data <engine_data>` to next request.
    7. url: :ref:`standard result <standard result>`
    """

    __slots__ = (
        '_merged_results',
        'infoboxes',
        'suggestions',
        'answers',
        'corrections',
        '_number_of_results',
        '_closed',
        'paging',
        'unresponsive_engines',
        'timings',
        'redirect_url',
        'engine_data',
        'on_result',
        '_lock',
    )

    def __init__(self):
        super().__init__()
        self._merged_results = []
        self.infoboxes = Infoboxes()
        self.suggestions = Suggestions()
        self.answers = Answers()
        self.corrections = Corrections()
        self._number_of_results = []
        self.engine_data = defaultdict(dict)
        self._closed = False
        self.paging = False
        self.unresponsive_engines: Set[UnresponsiveEngine] = set()
        self.timings: List[Timing] = []
        self.redirect_url = None
        self.on_result = lambda _: True
        self._lock = RLock()

    def extend(self, engine_name, results):  # pylint: disable=too-many-branches
        """Add a result item to the container."""
        if self._closed:
            return

        standard_result_count = 0
        error_msgs = set()
        for result in list(results):
            result['engine'] = engine_name
            if is_suggestion(result) and self.on_result(result):
                self.suggestions.add(result['suggestion'])
            elif is_answer(result) and self.on_result(result):
                self.answers.add(result)
            elif is_correction(result) and self.on_result(result):
                self.corrections.add(result['correction'])
            elif is_infobox(result) and self.on_result(result):
                self._merge_infobox(result)
            elif is_number_of_results(result) and self.on_result(result):
                self._number_of_results.append(result['number_of_results'])
            elif is_engine_data(result) and self.on_result(result):
                self.engine_data[engine_name][result['key']] = result['engine_data']
            elif is_standard_result(result):
                # standard result (url, title, content)
                if not self._is_valid_url_result(result, error_msgs):
                    continue
                # normalize the result
                self._normalize_url_result(result)
                # call on_result call searx.search.SearchWithPlugins._on_result
                # which calls the plugins
                if not self.on_result(result):
                    continue
                self.__merge_url_result(result, standard_result_count + 1)
                standard_result_count += 1
            elif self.on_result(result):
                self.__merge_result_no_url(result, standard_result_count + 1)
                standard_result_count += 1

        if len(error_msgs) > 0:
            for msg in error_msgs:
                count_error(engine_name, 'some results are invalids: ' + msg, secondary=True)

        if engine_name in engines:
            histogram_observe(standard_result_count, 'engine', engine_name, 'result', 'count')

        if not self.paging and standard_result_count > 0 and engine_name in engines and engines[engine_name].paging:
            self.paging = True

    def _merge_infobox(self, infobox):
        add_infobox = True
        infobox_id = infobox.get('id', None)
        infobox['engines'] = set([infobox['engine']])
        if infobox_id is not None:
            parsed_url_infobox_id = urlparse(infobox_id)
            with self._lock:
                for existingIndex in self.infoboxes:
                    if compare_urls(urlparse(existingIndex.get('id', '')), parsed_url_infobox_id):
                        merge_two_infoboxes(existingIndex, infobox)
                        add_infobox = False

        if add_infobox:
            self.infoboxes.append(infobox)

    def _is_valid_url_result(self, result, error_msgs):
        if 'url' in result:
            if not isinstance(result['url'], str):
                logger.debug('result: invalid URL: %s', str(result))
                error_msgs.add('invalid URL')
                return False

        if 'title' in result and not isinstance(result['title'], str):
            logger.debug('result: invalid title: %s', str(result))
            error_msgs.add('invalid title')
            return False

        if 'content' in result:
            if not isinstance(result['content'], str):
                logger.debug('result: invalid content: %s', str(result))
                error_msgs.add('invalid content')
                return False

        return True

    def _normalize_url_result(self, result):
        """Return True if the result is valid"""
        result['parsed_url'] = urlparse(result['url'])

        # if the result has no scheme, use http as default
        if not result['parsed_url'].scheme:
            result['parsed_url'] = result['parsed_url']._replace(scheme="http")
            result['url'] = result['parsed_url'].geturl()

        # avoid duplicate content between the content and title fields
        if result.get('content') == result.get('title'):
            del result['content']

        # make sure there is a template
        if 'template' not in result:
            result['template'] = 'default.html'

        # strip multiple spaces and cariage returns from content
        if result.get('content'):
            result['content'] = WHITESPACE_REGEX.sub(' ', result['content'])

    def __merge_url_result(self, result, position):
        result['engines'] = set([result['engine']])
        with self._lock:
            duplicated = self.__find_duplicated_http_result(result)
            if duplicated:
                self.__merge_duplicated_http_result(duplicated, result, position)
                return

            # if there is no duplicate found, append result
            result['positions'] = [position]
            self._merged_results.append(result)

    def __find_duplicated_http_result(self, result):
        result_template = result.get('template')
        for merged_result in self._merged_results:
            if 'parsed_url' not in merged_result:
                continue
            if compare_urls(result['parsed_url'], merged_result['parsed_url']) and result_template == merged_result.get(
                'template'
            ):
                if result_template != 'images.html':
                    # not an image, same template, same url : it's a duplicate
                    return merged_result
                # it's an image
                # it's a duplicate if the parsed_url, template and img_src are differents
                if result.get('img_src', '') == merged_result.get('img_src', ''):
                    return merged_result
        return None

    def __merge_duplicated_http_result(self, duplicated, result, position):
        # using content with more text
        if result_content_len(result.get('content', '')) > result_content_len(duplicated.get('content', '')):
            duplicated['content'] = result['content']

        # merge all result's parameters not found in duplicate
        for key in result.keys():
            if not duplicated.get(key):
                duplicated[key] = result.get(key)

        # add the new position
        duplicated['positions'].append(position)

        # add engine to list of result-engines
        duplicated['engines'].add(result['engine'])

        # using https if possible
        if duplicated['parsed_url'].scheme != 'https' and result['parsed_url'].scheme == 'https':
            duplicated['url'] = result['parsed_url'].geturl()
            duplicated['parsed_url'] = result['parsed_url']

    def __merge_result_no_url(self, result, position):
        result['engines'] = set([result['engine']])
        result['positions'] = [position]
        with self._lock:
            self._merged_results.append(result)

    def close(self):
        self._closed = True

        for result in self._merged_results:
            score = result_score(result)
            result['score'] = score
            for result_engine in result['engines']:
                counter_add(score, 'engine', result_engine, 'score')

        results = sorted(self._merged_results, key=itemgetter('score'), reverse=True)

        # pass 2 : group results by category and template
        gresults = []
        categoryPositions = {}

        for res in results:
            # pylint: disable=fixme
            # FIXME : handle more than one category per engine
            engine = engines[res['engine']]
            res['category'] = engine.categories[0] if len(engine.categories) > 0 else ''

            # FIXME : handle more than one category per engine
            category = (
                res['category']
                + ':'
                + res.get('template', '')
                + ':'
                + ('img_src' if 'img_src' in res or 'thumbnail' in res else '')
            )

            current = None if category not in categoryPositions else categoryPositions[category]

            # group with previous results using the same category
            # if the group can accept more result and is not too far
            # from the current position
            if current is not None and (current['count'] > 0) and (len(gresults) - current['index'] < 20):
                # group with the previous results using
                # the same category with this one
                index = current['index']
                gresults.insert(index, res)

                # update every index after the current one
                # (including the current one)
                for k in categoryPositions:  # pylint: disable=consider-using-dict-items
                    v = categoryPositions[k]['index']
                    if v >= index:
                        categoryPositions[k]['index'] = v + 1

                # update this category
                current['count'] -= 1

            else:
                # same category
                gresults.append(res)

                # update categoryIndex
                categoryPositions[category] = {'index': len(gresults), 'count': 8}

        # update _merged_results
        self._merged_results = gresults

    def get_ordered_results(self):
        if not self._closed:
            self.close()
        return self._merged_results

    def results_length(self):
        return len(self._merged_results)

    def results_number(self):
        resultnum_sum = sum(self._number_of_results)
        if not resultnum_sum or not self._number_of_results:
            return 0
        return resultnum_sum / len(self._number_of_results)

    def add_unresponsive_engine(self, engine_name: str, error_type: str, suspended: bool = False):
        if engines[engine_name].display_error_messages:
            self.unresponsive_engines.add(UnresponsiveEngine(engine_name, error_type, suspended))

    def add_timing(self, engine_name: str, engine_time: float, page_load_time: float):
        self.timings.append(Timing(engine_name, total=engine_time, load=page_load_time))

    def get_timings(self):
        return self.timings
