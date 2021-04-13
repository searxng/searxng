
'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2013- by Adam Tauber, <asciimoo@gmail.com>
'''

import sys
import threading
from os.path import realpath, dirname
from babel.localedata import locale_identifiers
from urllib.parse import urlparse
from flask_babel import gettext
from operator import itemgetter
from searx import settings
from searx import logger
from searx.data import ENGINES_LANGUAGES
from searx.exceptions import SearxEngineResponseException
from searx.network import get, initialize as initialize_network, set_context_network_name
from searx.utils import load_module, match_language, get_engine_from_settings, gen_useragent


logger = logger.getChild('engines')

engine_dir = dirname(realpath(__file__))

engines = {}

categories = {'general': []}

babel_langs = [lang_parts[0] + '-' + lang_parts[-1] if len(lang_parts) > 1 else lang_parts[0]
               for lang_parts in (lang_code.split('_') for lang_code in locale_identifiers())]

engine_shortcuts = {}
engine_default_args = {'paging': False,
                       'categories': ['general'],
                       'supported_languages': [],
                       'safesearch': False,
                       'timeout': settings['outgoing']['request_timeout'],
                       'shortcut': '-',
                       'disabled': False,
                       'enable_http': False,
                       'time_range_support': False,
                       'engine_type': 'online',
                       'display_error_messages': True,
                       'tokens': []}


def load_engine(engine_data):
    engine_name = engine_data['name']
    if '_' in engine_name:
        logger.error('Engine name contains underscore: "{}"'.format(engine_name))
        sys.exit(1)

    if engine_name.lower() != engine_name:
        logger.warn('Engine name is not lowercase: "{}", converting to lowercase'.format(engine_name))
        engine_name = engine_name.lower()
        engine_data['name'] = engine_name

    engine_module = engine_data['engine']

    try:
        engine = load_module(engine_module + '.py', engine_dir)
    except (SyntaxError, KeyboardInterrupt, SystemExit, SystemError, ImportError, RuntimeError):
        logger.exception('Fatal exception in engine "{}"'.format(engine_module))
        sys.exit(1)
    except:
        logger.exception('Cannot load engine "{}"'.format(engine_module))
        return None

    for param_name, param_value in engine_data.items():
        if param_name == 'engine':
            pass
        elif param_name == 'categories':
            if param_value == 'none':
                engine.categories = []
            else:
                engine.categories = list(map(str.strip, param_value.split(',')))
        else:
            setattr(engine, param_name, param_value)

    for arg_name, arg_value in engine_default_args.items():
        if not hasattr(engine, arg_name):
            setattr(engine, arg_name, arg_value)

    # checking required variables
    for engine_attr in dir(engine):
        if engine_attr.startswith('_'):
            continue
        if engine_attr == 'inactive' and getattr(engine, engine_attr) is True:
            return None
        if getattr(engine, engine_attr) is None:
            logger.error('Missing engine config attribute: "{0}.{1}"'
                         .format(engine.name, engine_attr))
            sys.exit(1)

    # assign supported languages from json file
    if engine_data['name'] in ENGINES_LANGUAGES:
        setattr(engine, 'supported_languages', ENGINES_LANGUAGES[engine_data['name']])

    # find custom aliases for non standard language codes
    if hasattr(engine, 'supported_languages'):
        if hasattr(engine, 'language_aliases'):
            language_aliases = getattr(engine, 'language_aliases')
        else:
            language_aliases = {}

        for engine_lang in getattr(engine, 'supported_languages'):
            iso_lang = match_language(engine_lang, babel_langs, fallback=None)
            if iso_lang and iso_lang != engine_lang and not engine_lang.startswith(iso_lang) and \
               iso_lang not in getattr(engine, 'supported_languages'):
                language_aliases[iso_lang] = engine_lang

        setattr(engine, 'language_aliases', language_aliases)

    # language_support
    setattr(engine, 'language_support', len(getattr(engine, 'supported_languages', [])) > 0)

    # assign language fetching method if auxiliary method exists
    if hasattr(engine, '_fetch_supported_languages'):
        headers = {
            'User-Agent': gen_useragent(),
            'Accept-Language': 'ja-JP,ja;q=0.8,en-US;q=0.5,en;q=0.3',  # bing needs a non-English language
        }
        setattr(engine, 'fetch_supported_languages',
                lambda: engine._fetch_supported_languages(get(engine.supported_languages_url, headers=headers)))

    engine.stats = {
        'sent_search_count': 0,  # sent search
        'search_count': 0,  # succesful search
        'result_count': 0,
        'engine_time': 0,
        'engine_time_count': 0,
        'score_count': 0,
        'errors': 0
    }

    engine_type = getattr(engine, 'engine_type', 'online')

    if engine_type != 'offline':
        engine.stats['page_load_time'] = 0
        engine.stats['page_load_count'] = 0

    # tor related settings
    if settings['outgoing'].get('using_tor_proxy'):
        # use onion url if using tor.
        if hasattr(engine, 'onion_url'):
            engine.search_url = engine.onion_url + getattr(engine, 'search_path', '')
    elif 'onions' in engine.categories:
        # exclude onion engines if not using tor.
        return None

    engine.timeout += settings['outgoing'].get('extra_proxy_timeout', 0)

    for category_name in engine.categories:
        categories.setdefault(category_name, []).append(engine)

    if engine.shortcut in engine_shortcuts:
        logger.error('Engine config error: ambigious shortcut: {0}'.format(engine.shortcut))
        sys.exit(1)

    engine_shortcuts[engine.shortcut] = engine.name

    return engine


def to_percentage(stats, maxvalue):
    for engine_stat in stats:
        if maxvalue:
            engine_stat['percentage'] = int(engine_stat['avg'] / maxvalue * 100)
        else:
            engine_stat['percentage'] = 0
    return stats


def get_engines_stats(preferences):
    # TODO refactor
    pageloads = []
    engine_times = []
    results = []
    scores = []
    errors = []
    scores_per_result = []

    max_pageload = max_engine_times = max_results = max_score = max_errors = max_score_per_result = 0  # noqa
    for engine in engines.values():
        if not preferences.validate_token(engine):
            continue

        if engine.stats['search_count'] == 0:
            continue

        results_num = \
            engine.stats['result_count'] / float(engine.stats['search_count'])

        if engine.stats['engine_time_count'] != 0:
            this_engine_time = engine.stats['engine_time'] / float(engine.stats['engine_time_count'])  # noqa
        else:
            this_engine_time = 0

        if results_num:
            score = engine.stats['score_count'] / float(engine.stats['search_count'])  # noqa
            score_per_result = score / results_num
        else:
            score = score_per_result = 0.0

        if engine.engine_type != 'offline':
            load_times = 0
            if engine.stats['page_load_count'] != 0:
                load_times = engine.stats['page_load_time'] / float(engine.stats['page_load_count'])  # noqa
            max_pageload = max(load_times, max_pageload)
            pageloads.append({'avg': load_times, 'name': engine.name})

        max_engine_times = max(this_engine_time, max_engine_times)
        max_results = max(results_num, max_results)
        max_score = max(score, max_score)
        max_score_per_result = max(score_per_result, max_score_per_result)
        max_errors = max(max_errors, engine.stats['errors'])

        engine_times.append({'avg': this_engine_time, 'name': engine.name})
        results.append({'avg': results_num, 'name': engine.name})
        scores.append({'avg': score, 'name': engine.name})
        errors.append({'avg': engine.stats['errors'], 'name': engine.name})
        scores_per_result.append({
            'avg': score_per_result,
            'name': engine.name
        })

    pageloads = to_percentage(pageloads, max_pageload)
    engine_times = to_percentage(engine_times, max_engine_times)
    results = to_percentage(results, max_results)
    scores = to_percentage(scores, max_score)
    scores_per_result = to_percentage(scores_per_result, max_score_per_result)
    errors = to_percentage(errors, max_errors)

    return [
        (
            gettext('Engine time (sec)'),
            sorted(engine_times, key=itemgetter('avg'))
        ),
        (
            gettext('Page loads (sec)'),
            sorted(pageloads, key=itemgetter('avg'))
        ),
        (
            gettext('Number of results'),
            sorted(results, key=itemgetter('avg'), reverse=True)
        ),
        (
            gettext('Scores'),
            sorted(scores, key=itemgetter('avg'), reverse=True)
        ),
        (
            gettext('Scores per result'),
            sorted(scores_per_result, key=itemgetter('avg'), reverse=True)
        ),
        (
            gettext('Errors'),
            sorted(errors, key=itemgetter('avg'), reverse=True)
        ),
    ]


def load_engines(engine_list):
    global engines, engine_shortcuts
    engines.clear()
    engine_shortcuts.clear()
    for engine_data in engine_list:
        engine = load_engine(engine_data)
        if engine is not None:
            engines[engine.name] = engine
    return engines


def initialize_engines(engine_list):
    load_engines(engine_list)
    initialize_network(engine_list, settings['outgoing'])

    def engine_init(engine_name, init_fn):
        try:
            set_context_network_name(engine_name)
            init_fn(get_engine_from_settings(engine_name))
        except SearxEngineResponseException as exc:
            logger.warn('%s engine: Fail to initialize // %s', engine_name, exc)
        except Exception:
            logger.exception('%s engine: Fail to initialize', engine_name)
        else:
            logger.debug('%s engine: Initialized', engine_name)

    for engine_name, engine in engines.items():
        if hasattr(engine, 'init'):
            init_fn = getattr(engine, 'init')
            if init_fn:
                logger.debug('%s engine: Starting background initialization', engine_name)
                threading.Thread(target=engine_init, args=(engine_name, init_fn)).start()
