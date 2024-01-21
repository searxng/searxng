from os import getenv
from searx import settings, engines, settings
from searx.search import SearchQuery, Search, EngineRef, initialize
from tests import SearxTestCase
from typing import Tuple, Optional
import sys
import logging
from flask import Flask
from dotenv import load_dotenv, find_dotenv

# Root directeory .env.test file
load_dotenv(find_dotenv("../../.env.test", raise_error_if_not_found=False))

logger = logging.getLogger('integration-test')
logger.level = logging.INFO
stream_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stream_handler)

SAFESEARCH = 0
PAGENO = 1


def test_single_engine(app: Flask, engine_name: str) -> Tuple[str, Optional[Exception], int]:
    logger.debug(f'Testing Engine: {engine_name}')
    try:
        with app.test_request_context():
            # test your app context code
            search_query = SearchQuery(
                'test', [EngineRef(engine_name, 'general')], 'en-US', SAFESEARCH, PAGENO, None, None
            )
            search = Search(search_query)
            info = search.search()
            return (engine_name, None, info.results_length())
    except Exception as e:
        return (engine_name, e, 0)


def get_specific_engines() -> list[str]:
    integration_engines = getenv("INTEGRATION_TEST_ENGINES")
    if integration_engines is None or integration_engines == '':
        return []
    return integration_engines.split(',')


class TestEnginesSingleSearch(SearxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        specific_engines = get_specific_engines()

        if len(specific_engines) > 0:
            cls.engines = [eng for eng in settings['engines'] if eng['name'] in specific_engines]
        else:
            cls.engines = settings['engines']

        cls.engine_names = [eng['name'] for eng in cls.engines]

        initialize(cls.engines)

    @classmethod
    def tearDownClass(cls):
        settings['outgoing']['using_tor_proxy'] = False
        settings['outgoing']['extra_proxy_timeout'] = 0

    def test_all_engines(self):
        results = [test_single_engine(self.app, engine_name) for engine_name in self.engine_names]
        engines_passed = []
        engines_exception = []
        engines_no_results = []
        for r in results:
            if r[1] is not None:
                engines_exception.append(r)
            elif r[2] <= 0:
                engines_no_results.append(r)
            else:
                engines_passed.append(r)

        def log_results(lst, name: str):
            logger.info(f'{name}: {len(lst)}')
            for e in lst:
                logger.info(f'{name}: engine: {e[0]}')

        log_results(engines_passed, 'engines_passed')
        log_results(engines_exception, 'engines_exception')
        log_results(engines_no_results, 'engines_no_results')

        self.assertEqual(len(engines_exception), 0)
        self.assertEqual(len(engines_no_results), 0)
