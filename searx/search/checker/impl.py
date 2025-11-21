# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring, invalid-name

import gc
import time
import typing
import types
import functools
import itertools
from timeit import default_timer
from urllib.parse import urlparse

import re
import httpx

from searx import network, logger
from searx.utils import gen_useragent, detect_language
from searx.results import ResultContainer
from searx.search.models import SearchQuery, EngineRef
from searx.search.processors import EngineProcessor
from searx.metrics import counter_inc


logger = logger.getChild('searx.search.checker')

HTML_TAGS = [
    # fmt: off
    'embed', 'iframe', 'object', 'param', 'picture', 'source', 'svg', 'math', 'canvas', 'noscript', 'script',
    'del', 'ins', 'area', 'audio', 'img', 'map', 'track', 'video', 'a', 'abbr', 'b', 'bdi', 'bdo', 'br', 'cite',
    'code', 'data', 'dfn', 'em', 'i', 'kdb', 'mark', 'q', 'rb', 'rp', 'rt', 'rtc', 'ruby', 's', 'samp', 'small',
    'span', 'strong', 'sub', 'sup', 'time', 'u', 'var', 'wbr', 'style', 'blockquote', 'dd', 'div', 'dl', 'dt',
    'figcaption', 'figure', 'hr', 'li', 'ol', 'p', 'pre', 'ul', 'button', 'datalist', 'fieldset', 'form', 'input',
    'label', 'legend', 'meter', 'optgroup', 'option', 'output', 'progress', 'select', 'textarea', 'applet',
    'frame', 'frameset'
    # fmt: on
]


def get_check_no_html():
    rep = ['<' + tag + r'[^\>]*>' for tag in HTML_TAGS]
    rep += ['</' + tag + '>' for tag in HTML_TAGS]
    pattern = re.compile('|'.join(rep))

    def f(text):
        return pattern.search(text.lower()) is None

    return f


_check_no_html = get_check_no_html()


def _is_url(url):
    try:
        result = urlparse(url)
    except ValueError:
        return False
    if result.scheme not in ('http', 'https'):
        return False
    return True


@functools.lru_cache(maxsize=8192)
def _download_and_check_if_image(image_url: str) -> bool:
    """Download an URL and check if the Content-Type starts with "image/"
    This function should not be called directly: use _is_url_image
    otherwise the cache of functools.lru_cache contains data: URL which might be huge.
    """
    retry = 3

    while retry > 0:
        a = default_timer()
        try:
            # use "image_proxy" (avoid HTTP/2)
            network.set_timeout_for_thread(2)
            network.set_context_network_name('image_proxy')
            r = network.get(
                image_url,
                timeout=10.0,
                allow_redirects=True,
                headers={
                    'User-Agent': gen_useragent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US;q=0.5,en;q=0.3',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-GPC': '1',
                    'Cache-Control': 'max-age=0',
                },
            )
            if r.status_code == 200:
                is_image = r.headers.get('content-type', '').startswith('image/')
            else:
                is_image = False
            del r
            return is_image
        except httpx.TimeoutException:
            logger.error('Timeout for %s: %i', image_url, int(default_timer() - a))
            time.sleep(1)
            retry -= 1
        except httpx.HTTPStatusError as e:
            logger.error('Exception for %s: HTTP status=%i', image_url, e.response.status_code)
        except httpx.HTTPError as e:
            logger.error('Exception for %s: %s, %s', image_url, e.__class__.__name__, ",".join(e.args))
            return False
    return False


def _is_url_image(image_url) -> bool:
    """Normalize image_url"""
    if not isinstance(image_url, str):
        return False

    if image_url.startswith('//'):
        image_url = 'https:' + image_url

    if image_url.startswith('data:'):
        return image_url.startswith('data:image/')

    if not _is_url(image_url):
        return False

    return _download_and_check_if_image(image_url)


def _search_query_to_dict(search_query: SearchQuery) -> typing.Dict[str, typing.Any]:
    return {
        'query': search_query.query,
        'lang': search_query.lang,
        'pageno': search_query.pageno,
        'safesearch': search_query.safesearch,
        'time_range': search_query.time_range,
    }


def _search_query_diff(
    sq1: SearchQuery, sq2: SearchQuery
) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, typing.Any]]:
    param1 = _search_query_to_dict(sq1)
    param2 = _search_query_to_dict(sq2)
    common = {}
    diff = {}
    for k, value1 in param1.items():
        value2 = param2[k]
        if value1 == value2:
            common[k] = value1
        else:
            diff[k] = (value1, value2)
    return (common, diff)


class TestResults:  # pylint: disable=missing-class-docstring

    __slots__ = 'errors', 'logs', 'languages'

    def __init__(self):
        self.errors: typing.Dict[str, typing.List[str]] = {}
        self.logs: typing.Dict[str, typing.List[typing.Any]] = {}
        self.languages: typing.Set[str] = set()

    def add_error(self, test, message, *args):
        # message to self.errors
        errors_for_test = self.errors.setdefault(test, [])
        if message not in errors_for_test:
            errors_for_test.append(message)
        # (message, *args) to self.logs
        logs_for_test = self.logs.setdefault(test, [])
        if (message, *args) not in logs_for_test:
            logs_for_test.append((message, *args))

    def add_language(self, language):
        self.languages.add(language)

    @property
    def successful(self):
        return len(self.errors) == 0

    def __iter__(self):
        for test_name, errors in self.errors.items():
            for error in sorted(errors):
                yield (test_name, error)


class ResultContainerTests:  # pylint: disable=missing-class-docstring

    __slots__ = 'test_name', 'search_query', 'result_container', 'languages', 'stop_test', 'test_results'

    def __init__(
        self, test_results: TestResults, test_name: str, search_query: SearchQuery, result_container: ResultContainer
    ):
        self.test_name = test_name
        self.search_query = search_query
        self.result_container = result_container
        self.languages: typing.Set[str] = set()
        self.test_results = test_results
        self.stop_test = False

    @property
    def result_urls(self):
        results = self.result_container.get_ordered_results()
        return [result['url'] for result in results if 'url' in result]

    def _record_error(self, message: str, *args) -> None:
        sq = _search_query_to_dict(self.search_query)
        sqstr = ' '.join(['{}={!r}'.format(k, v) for k, v in sq.items()])
        self.test_results.add_error(self.test_name, message, *args, '(' + sqstr + ')')

    def _add_language(self, text: str) -> typing.Optional[str]:
        langStr = detect_language(text)
        if langStr:
            self.languages.add(langStr)
            self.test_results.add_language(langStr)

    def _check_result(self, result):
        if not _check_no_html(result.get('title', '')):
            self._record_error('HTML in title', repr(result.get('title', '')))
        if not _check_no_html(result.get('content', '')):
            self._record_error('HTML in content', repr(result.get('content', '')))
        if result.get('url') is None:
            self._record_error('url is None')

        self._add_language(result.get('title', ''))
        self._add_language(result.get('content', ''))

        template = result.get('template', 'default.html')
        if template == 'default.html':
            return
        if template == 'code.html':
            return
        if template == 'torrent.html':
            return
        if template == 'map.html':
            return
        if template == 'images.html':
            thumbnail_src = result.get('thumbnail_src')
            if thumbnail_src is not None:
                if not _is_url_image(thumbnail_src):
                    self._record_error('thumbnail_src URL is invalid', thumbnail_src)
            elif not _is_url_image(result.get('img_src')):
                self._record_error('img_src URL is invalid', result.get('img_src'))
        if template == 'videos.html' and not _is_url_image(result.get('thumbnail')):
            self._record_error('thumbnail URL is invalid', result.get('img_src'))

    def _check_results(self, results: list):
        for result in results:
            self._check_result(result)

    def _check_answers(self, answers):
        for answer in answers:
            if not _check_no_html(answer):
                self._record_error('HTML in answer', answer)

    def _check_infoboxes(self, infoboxes):
        for infobox in infoboxes:
            if not _check_no_html(infobox.get('content', '')):
                self._record_error('HTML in infobox content', infobox.get('content', ''))
            self._add_language(infobox.get('content', ''))
            for attribute in infobox.get('attributes', {}):
                if not _check_no_html(attribute.get('value', '')):
                    self._record_error('HTML in infobox attribute value', attribute.get('value', ''))

    def check_basic(self):
        if len(self.result_container.unresponsive_engines) > 0:
            for message in self.result_container.unresponsive_engines:
                self._record_error(message[1] + ' ' + (message[2] or ''))
            self.stop_test = True
            return

        results = self.result_container.get_ordered_results()
        if len(results) > 0:
            self._check_results(results)

        if len(self.result_container.answers) > 0:
            self._check_answers(self.result_container.answers)

        if len(self.result_container.infoboxes) > 0:
            self._check_infoboxes(self.result_container.infoboxes)

    def has_infobox(self):
        """Check the ResultContainer has at least one infobox"""
        if len(self.result_container.infoboxes) == 0:
            self._record_error('No infobox')

    def has_answer(self):
        """Check the ResultContainer has at least one answer"""
        if len(self.result_container.answers) == 0:
            self._record_error('No answer')

    def has_language(self, lang):
        """Check at least one title or content of the results is written in the `lang`.

        Detected using pycld3, may be not accurate"""
        if lang not in self.languages:
            self._record_error(lang + ' not found')

    def not_empty(self):
        """Check the ResultContainer has at least one answer or infobox or result"""
        result_types = set()
        results = self.result_container.get_ordered_results()
        if len(results) > 0:
            result_types.add('results')

        if len(self.result_container.answers) > 0:
            result_types.add('answers')

        if len(self.result_container.infoboxes) > 0:
            result_types.add('infoboxes')

        if len(result_types) == 0:
            self._record_error('No result')

    def one_title_contains(self, title: str):
        """Check one of the title contains `title` (case insensitive comparison)"""
        title = title.lower()
        for result in self.result_container.get_ordered_results():
            if title in result['title'].lower():
                return
        self._record_error(('{!r} not found in the title'.format(title)))


class CheckerTests:  # pylint: disable=missing-class-docstring, too-few-public-methods

    __slots__ = 'test_results', 'test_name', 'result_container_tests_list'

    def __init__(
        self, test_results: TestResults, test_name: str, result_container_tests_list: typing.List[ResultContainerTests]
    ):
        self.test_results = test_results
        self.test_name = test_name
        self.result_container_tests_list = result_container_tests_list

    def unique_results(self):
        """Check the results of each ResultContainer is unique"""
        urls_list = [rct.result_urls for rct in self.result_container_tests_list]
        if len(urls_list[0]) > 0:
            # results on the first page
            for i, urls_i in enumerate(urls_list):
                for j, urls_j in enumerate(urls_list):
                    if i < j and urls_i == urls_j:
                        common, diff = _search_query_diff(
                            self.result_container_tests_list[i].search_query,
                            self.result_container_tests_list[j].search_query,
                        )
                        common_str = ' '.join(['{}={!r}'.format(k, v) for k, v in common.items()])
                        diff1_str = ', '.join(['{}={!r}'.format(k, v1) for (k, (v1, v2)) in diff.items()])
                        diff2_str = ', '.join(['{}={!r}'.format(k, v2) for (k, (v1, v2)) in diff.items()])
                        self.test_results.add_error(
                            self.test_name,
                            'results are identical for {} and {} ({})'.format(diff1_str, diff2_str, common_str),
                        )


class Checker:  # pylint: disable=missing-class-docstring

    __slots__ = 'processor', 'tests', 'test_results'

    def __init__(self, processor: EngineProcessor):
        self.processor = processor
        self.tests = self.processor.get_tests()
        self.test_results = TestResults()

    @property
    def engineref_list(self):
        engine_name = self.processor.engine_name
        engine_category = self.processor.engine.categories[0]
        return [EngineRef(engine_name, engine_category)]

    @staticmethod
    def search_query_matrix_iterator(engineref_list, matrix):
        p = []
        for name, values in matrix.items():
            if isinstance(values, (tuple, list)):
                l = [(name, value) for value in values]
            else:
                l = [(name, values)]
            p.append(l)

        for kwargs in itertools.product(*p):
            kwargs = dict(kwargs)
            query = kwargs['query']
            params = dict(kwargs)
            del params['query']
            yield SearchQuery(query, engineref_list, **params)

    def call_test(self, obj, test_description):
        if isinstance(test_description, (tuple, list)):
            method, args = test_description[0], test_description[1:]
        else:
            method = test_description
            args = ()
        if isinstance(method, str) and hasattr(obj, method):
            getattr(obj, method)(*args)
        elif isinstance(method, types.FunctionType):
            method(*args)
        else:
            self.test_results.add_error(
                obj.test_name,
                'method {!r} ({}) not found for {}'.format(method, method.__class__.__name__, obj.__class__.__name__),
            )

    def call_tests(self, obj, test_descriptions):
        for test_description in test_descriptions:
            self.call_test(obj, test_description)

    def search(self, search_query: SearchQuery) -> ResultContainer:
        result_container = ResultContainer()
        engineref_category = search_query.engineref_list[0].category
        params = self.processor.get_params(search_query, engineref_category)
        if params is not None:
            counter_inc('engine', search_query.engineref_list[0].name, 'search', 'count', 'sent')
            self.processor.search(search_query.query, params, result_container, default_timer(), 5)
        return result_container

    def get_result_container_tests(self, test_name: str, search_query: SearchQuery) -> ResultContainerTests:
        result_container = self.search(search_query)
        result_container_check = ResultContainerTests(self.test_results, test_name, search_query, result_container)
        result_container_check.check_basic()
        return result_container_check

    def run_test(self, test_name):
        test_parameters = self.tests[test_name]
        search_query_list = list(Checker.search_query_matrix_iterator(self.engineref_list, test_parameters['matrix']))
        rct_list = [self.get_result_container_tests(test_name, search_query) for search_query in search_query_list]
        stop_test = False
        if 'result_container' in test_parameters:
            for rct in rct_list:
                stop_test = stop_test or rct.stop_test
                if not rct.stop_test:
                    self.call_tests(rct, test_parameters['result_container'])
        if not stop_test:
            if 'test' in test_parameters:
                checker_tests = CheckerTests(self.test_results, test_name, rct_list)
                self.call_tests(checker_tests, test_parameters['test'])

    def run(self):
        for test_name in self.tests:
            self.run_test(test_name)
            # clear cache
            _download_and_check_if_image.cache_clear()
            # force a garbage collector
            gc.collect()
