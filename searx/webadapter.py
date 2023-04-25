from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from searx.exceptions import SearxParameterException
from searx.webutils import VALID_LANGUAGE_CODE
from searx.query import RawTextQuery
from searx.engines import categories, engines
from searx.search import SearchQuery, EngineRef
from searx.preferences import Preferences, is_locked
from searx.utils import detect_language


# remove duplicate queries.
# FIXME: does not fix "!music !soundcloud", because the categories are 'none' and 'music'
def deduplicate_engineref_list(engineref_list: List[EngineRef]) -> List[EngineRef]:
    engineref_dict = {q.category + '|' + q.name: q for q in engineref_list}
    return list(engineref_dict.values())


def validate_engineref_list(
    engineref_list: List[EngineRef], preferences: Preferences
) -> Tuple[List[EngineRef], List[EngineRef], List[EngineRef]]:
    """Validate query_engines according to the preferences

    Returns:
        List[EngineRef]: list of existing engines with a validated token
        List[EngineRef]: list of unknown engine
        List[EngineRef]: list of engine with invalid token according to the preferences
    """
    valid = []
    unknown = []
    no_token = []
    for engineref in engineref_list:
        if engineref.name not in engines:
            unknown.append(engineref)
            continue

        engine = engines[engineref.name]
        if not preferences.validate_token(engine):
            no_token.append(engineref)
            continue

        valid.append(engineref)
    return valid, unknown, no_token


def parse_pageno(form: Dict[str, str]) -> int:
    pageno_param = form.get('pageno', '1')
    if not pageno_param.isdigit() or int(pageno_param) < 1:
        raise SearxParameterException('pageno', pageno_param)
    return int(pageno_param)


def parse_lang(preferences: Preferences, form: Dict[str, str], raw_text_query: RawTextQuery) -> str:
    if is_locked('language'):
        return preferences.get_value('language')
    # get language
    # set specific language if set on request, query or preferences
    # TODO support search with multiple languages
    if len(raw_text_query.languages):
        query_lang = raw_text_query.languages[-1]
    elif 'language' in form:
        query_lang = form.get('language')
    else:
        query_lang = preferences.get_value('language')

    # check language
    if not VALID_LANGUAGE_CODE.match(query_lang) and query_lang != 'auto':
        raise SearxParameterException('language', query_lang)

    return query_lang


def parse_safesearch(preferences: Preferences, form: Dict[str, str]) -> int:
    if is_locked('safesearch'):
        return preferences.get_value('safesearch')

    if 'safesearch' in form:
        query_safesearch = form.get('safesearch')
        # first check safesearch
        if not query_safesearch.isdigit():
            raise SearxParameterException('safesearch', query_safesearch)
        query_safesearch = int(query_safesearch)
    else:
        query_safesearch = preferences.get_value('safesearch')

    # safesearch : second check
    if query_safesearch < 0 or query_safesearch > 2:
        raise SearxParameterException('safesearch', query_safesearch)

    return query_safesearch


def parse_time_range(form: Dict[str, str]) -> Optional[str]:
    query_time_range = form.get('time_range')
    # check time_range
    query_time_range = None if query_time_range in ('', 'None') else query_time_range
    if query_time_range not in (None, 'day', 'week', 'month', 'year'):
        raise SearxParameterException('time_range', query_time_range)
    return query_time_range


def parse_timeout(form: Dict[str, str], raw_text_query: RawTextQuery) -> Optional[float]:
    timeout_limit = raw_text_query.timeout_limit
    if timeout_limit is None:
        timeout_limit = form.get('timeout_limit')

    if timeout_limit is None or timeout_limit in ['None', '']:
        return None
    try:
        return float(timeout_limit)
    except ValueError as e:
        raise SearxParameterException('timeout_limit', timeout_limit) from e


def parse_category_form(query_categories: List[str], name: str, value: str) -> None:
    if name == 'categories':
        query_categories.extend(categ for categ in map(str.strip, value.split(',')) if categ in categories)
    elif name.startswith('category_'):
        category = name[9:]

        # if category is not found in list, skip
        if category not in categories:
            return

        if value != 'off':
            # add category to list
            query_categories.append(category)
        elif category in query_categories:
            # remove category from list if property is set to 'off'
            query_categories.remove(category)


def get_selected_categories(preferences: Preferences, form: Optional[Dict[str, str]]) -> List[str]:
    selected_categories = []

    if not is_locked('categories') and form is not None:
        for name, value in form.items():
            parse_category_form(selected_categories, name, value)

    # if no category is specified for this search,
    # using user-defined default-configuration which
    # (is stored in cookie)
    if not selected_categories:
        cookie_categories = preferences.get_value('categories')
        for ccateg in cookie_categories:
            selected_categories.append(ccateg)

    # if still no category is specified, using general
    # as default-category
    if not selected_categories:
        selected_categories = ['general']

    return selected_categories


def get_engineref_from_category_list(category_list: List[str], disabled_engines: List[str]) -> List[EngineRef]:
    result = []
    for categ in category_list:
        result.extend(
            EngineRef(engine.name, categ)
            for engine in categories[categ]
            if (engine.name, categ) not in disabled_engines
        )
    return result


def parse_generic(preferences: Preferences, form: Dict[str, str], disabled_engines: List[str]) -> List[EngineRef]:
    query_engineref_list = []
    query_categories = []

    # set categories/engines
    explicit_engine_list = False
    if not is_locked('categories'):
        # parse the form only if the categories are not locked
        for pd_name, pd in form.items():
            if pd_name == 'engines':
                pd_engines = [
                    EngineRef(engine_name, engines[engine_name].categories[0])
                    for engine_name in map(str.strip, pd.split(','))
                    if engine_name in engines
                ]
                if pd_engines:
                    query_engineref_list.extend(pd_engines)
                    explicit_engine_list = True
            else:
                parse_category_form(query_categories, pd_name, pd)

    if explicit_engine_list:
        # explicit list of engines with the "engines" parameter in the form
        if query_categories:
            # add engines from referenced by the "categories" parameter and the "category_*"" parameters
            query_engineref_list.extend(get_engineref_from_category_list(query_categories, disabled_engines))
    else:
        # no "engines" parameters in the form
        if not query_categories:
            # and neither "categories" parameter nor "category_*"" parameters in the form
            # -> get the categories from the preferences (the cookies or the settings)
            query_categories = get_selected_categories(preferences, None)

        # using all engines for that search, which are
        # declared under the specific categories
        query_engineref_list.extend(get_engineref_from_category_list(query_categories, disabled_engines))

    return query_engineref_list


def parse_engine_data(form):
    engine_data = defaultdict(dict)
    for k, v in form.items():
        if k.startswith("engine_data"):
            _, engine, key = k.split('-')
            engine_data[engine][key] = v
    return engine_data


def get_search_query_from_webapp(
    preferences: Preferences, form: Dict[str, str]
) -> Tuple[SearchQuery, RawTextQuery, List[EngineRef], List[EngineRef], str]:
    """Assemble data from preferences and request.form (from the HTML form) needed
    in a search query.

    The returned tuple consits of:

    1. instance of :py:obj:`searx.search.SearchQuery`
    2. instance of :py:obj:`searx.query.RawTextQuery`
    3. list of :py:obj:`searx.search.EngineRef` instances
    4. string with the *selected locale* of the query

    About language/locale: if the client selects the alias ``auto`` the
    ``SearchQuery`` object is build up by the :py:obj:`detected language
    <searx.utils.detect_language>`.  If language recognition does not have a
    match the language preferred by the :py:obj:`Preferences.client` is used.
    If client does not have a preference, the default ``all`` is used.

    The *selected locale* in the tuple always represents the selected
    language/locale and might differ from the language recognition.

    """
    # no text for the query ?
    if not form.get('q'):
        raise SearxParameterException('q', '')

    # set blocked engines
    disabled_engines = preferences.engines.get_disabled()

    # parse query, if tags are set, which change
    # the search engine or search-language
    raw_text_query = RawTextQuery(form['q'], disabled_engines)

    # set query
    query = raw_text_query.getQuery()
    query_pageno = parse_pageno(form)
    query_safesearch = parse_safesearch(preferences, form)
    query_time_range = parse_time_range(form)
    query_timeout = parse_timeout(form, raw_text_query)
    external_bang = raw_text_query.external_bang
    engine_data = parse_engine_data(form)

    query_lang = parse_lang(preferences, form, raw_text_query)
    selected_locale = query_lang

    if query_lang == 'auto':
        query_lang = detect_language(query, threshold=0.8, only_search_languages=True)
        query_lang = query_lang or preferences.client.locale_tag or 'all'

    if not is_locked('categories') and raw_text_query.specific:
        # if engines are calculated from query,
        # set categories by using that information
        query_engineref_list = raw_text_query.enginerefs
    else:
        # otherwise, using defined categories to
        # calculate which engines should be used
        query_engineref_list = parse_generic(preferences, form, disabled_engines)

    query_engineref_list = deduplicate_engineref_list(query_engineref_list)
    query_engineref_list, query_engineref_list_unknown, query_engineref_list_notoken = validate_engineref_list(
        query_engineref_list, preferences
    )

    return (
        SearchQuery(
            query,
            query_engineref_list,
            query_lang,
            query_safesearch,
            query_pageno,
            query_time_range,
            query_timeout,
            external_bang=external_bang,
            engine_data=engine_data,
        ),
        raw_text_query,
        query_engineref_list_unknown,
        query_engineref_list_notoken,
        selected_locale,
    )
