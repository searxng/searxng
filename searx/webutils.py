# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import pathlib
import csv
import hashlib
import hmac
import re
import inspect
import itertools
import json
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple, Dict, TYPE_CHECKING

from io import StringIO
from codecs import getincrementalencoder

from flask_babel import gettext, format_date  # type: ignore

from searx import logger, settings
from searx.engines import DEFAULT_CATEGORY

if TYPE_CHECKING:
    from searx.enginelib import Engine
    from searx.results import ResultContainer
    from searx.search import SearchQuery
    from searx.results import UnresponsiveEngine

VALID_LANGUAGE_CODE = re.compile(r'^[a-z]{2,3}(-[a-zA-Z]{2})?$')

logger = logger.getChild('webutils')

timeout_text = gettext('timeout')
parsing_error_text = gettext('parsing error')
http_protocol_error_text = gettext('HTTP protocol error')
network_error_text = gettext('network error')
ssl_cert_error_text = gettext("SSL error: certificate validation has failed")
exception_classname_to_text = {
    None: gettext('unexpected crash'),
    'timeout': timeout_text,
    'asyncio.TimeoutError': timeout_text,
    'httpx.TimeoutException': timeout_text,
    'httpx.ConnectTimeout': timeout_text,
    'httpx.ReadTimeout': timeout_text,
    'httpx.WriteTimeout': timeout_text,
    'httpx.HTTPStatusError': gettext('HTTP error'),
    'httpx.ConnectError': gettext("HTTP connection error"),
    'httpx.RemoteProtocolError': http_protocol_error_text,
    'httpx.LocalProtocolError': http_protocol_error_text,
    'httpx.ProtocolError': http_protocol_error_text,
    'httpx.ReadError': network_error_text,
    'httpx.WriteError': network_error_text,
    'httpx.ProxyError': gettext("proxy error"),
    'searx.exceptions.SearxEngineCaptchaException': gettext("CAPTCHA"),
    'searx.exceptions.SearxEngineTooManyRequestsException': gettext("too many requests"),
    'searx.exceptions.SearxEngineAccessDeniedException': gettext("access denied"),
    'searx.exceptions.SearxEngineAPIException': gettext("server API error"),
    'searx.exceptions.SearxEngineXPathException': parsing_error_text,
    'KeyError': parsing_error_text,
    'json.decoder.JSONDecodeError': parsing_error_text,
    'lxml.etree.ParserError': parsing_error_text,
    'ssl.SSLCertVerificationError': ssl_cert_error_text,  # for Python > 3.7
    'ssl.CertificateError': ssl_cert_error_text,  # for Python 3.7
}


def get_translated_errors(unresponsive_engines: Iterable[UnresponsiveEngine]):
    translated_errors = []

    for unresponsive_engine in unresponsive_engines:
        error_user_text = exception_classname_to_text.get(unresponsive_engine.error_type)
        if not error_user_text:
            error_user_text = exception_classname_to_text[None]
        error_msg = gettext(error_user_text)
        if unresponsive_engine.suspended:
            error_msg = gettext('Suspended') + ': ' + error_msg
        translated_errors.append((unresponsive_engine.engine, error_msg))

    return sorted(translated_errors, key=lambda e: e[0])


class CSVWriter:
    """A CSV writer which will write rows to CSV file "f", which is encoded in
    the given encoding."""

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow(row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.strip('\x00')
        # ... and re-encode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data.decode())
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def write_csv_response(csv: CSVWriter, rc: ResultContainer) -> None:
    """Write rows of the results to a query (``application/csv``) into a CSV
    table (:py:obj:`CSVWriter`).  First line in the table contain the column
    names.  The column "type" specifies the type, the following types are
    included in the table:

    - result
    - answer
    - suggestion
    - correction

    """

    results = rc.get_ordered_results()
    keys = ('title', 'url', 'content', 'host', 'engine', 'score', 'type')
    csv.writerow(keys)

    for row in results:
        row['host'] = row['parsed_url'].netloc
        row['type'] = 'result'
        csv.writerow([row.get(key, '') for key in keys])

    for a in rc.answers:
        row = {'title': a, 'type': 'answer'}
        csv.writerow([row.get(key, '') for key in keys])

    for a in rc.suggestions:
        row = {'title': a, 'type': 'suggestion'}
        csv.writerow([row.get(key, '') for key in keys])

    for a in rc.corrections:
        row = {'title': a, 'type': 'correction'}
        csv.writerow([row.get(key, '') for key in keys])


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, timedelta):
            return o.total_seconds()
        if isinstance(o, set):
            return list(o)
        return super().default(o)


def get_json_response(sq: SearchQuery, rc: ResultContainer) -> str:
    """Returns the JSON string of the results to a query (``application/json``)"""
    results = rc.number_of_results
    x = {
        'query': sq.query,
        'number_of_results': results,
        'results': rc.get_ordered_results(),
        'answers': list(rc.answers),
        'corrections': list(rc.corrections),
        'infoboxes': rc.infoboxes,
        'suggestions': list(rc.suggestions),
        'unresponsive_engines': get_translated_errors(rc.unresponsive_engines),
    }
    response = json.dumps(x, cls=JSONEncoder)
    return response


def get_themes(templates_path):
    """Returns available themes list."""
    return os.listdir(templates_path)


def get_hash_for_file(file: pathlib.Path) -> str:
    m = hashlib.sha1()
    with file.open('rb') as f:
        m.update(f.read())
    return m.hexdigest()


def get_static_files(static_path: str) -> Dict[str, str]:
    static_files: Dict[str, str] = {}
    static_path_path = pathlib.Path(static_path)

    def walk(path: pathlib.Path):
        for file in path.iterdir():
            if file.name.startswith('.'):
                # ignore hidden file
                continue
            if file.is_file():
                static_files[str(file.relative_to(static_path_path))] = get_hash_for_file(file)
            if file.is_dir() and file.name not in ('node_modules', 'src'):
                # ignore "src" and "node_modules" directories
                walk(file)

    walk(static_path_path)
    return static_files


def get_result_templates(templates_path):
    result_templates = set()
    templates_path_length = len(templates_path) + 1
    for directory, _, files in os.walk(templates_path):
        if directory.endswith('result_templates'):
            for filename in files:
                f = os.path.join(directory[templates_path_length:], filename)
                result_templates.add(f)
    return result_templates


def new_hmac(secret_key, url):
    return hmac.new(secret_key.encode(), url, hashlib.sha256).hexdigest()


def is_hmac_of(secret_key, value, hmac_to_check):
    hmac_of_value = new_hmac(secret_key, value)
    return len(hmac_of_value) == len(hmac_to_check) and hmac.compare_digest(hmac_of_value, hmac_to_check)


def prettify_url(url, max_length=74):
    if len(url) > max_length:
        chunk_len = int(max_length / 2 + 1)
        return '{0}[...]{1}'.format(url[:chunk_len], url[-chunk_len:])
    else:
        return url


def contains_cjko(s: str) -> bool:
    """This function check whether or not a string contains Chinese, Japanese,
    or Korean characters. It employs regex and uses the u escape sequence to
    match any character in a set of Unicode ranges.

    Args:
        s (str): string to be checked.

    Returns:
        bool: True if the input s contains the characters and False otherwise.
    """
    unicode_ranges = (
        '\u4e00-\u9fff'  # Chinese characters
        '\u3040-\u309f'  # Japanese hiragana
        '\u30a0-\u30ff'  # Japanese katakana
        '\u4e00-\u9faf'  # Japanese kanji
        '\uac00-\ud7af'  # Korean hangul syllables
        '\u1100-\u11ff'  # Korean hangul jamo
    )
    return bool(re.search(fr'[{unicode_ranges}]', s))


def regex_highlight_cjk(word: str) -> str:
    """Generate the regex pattern to match for a given word according
    to whether or not the word contains CJK characters or not.
    If the word is and/or contains CJK character, the regex pattern
    will match standalone word by taking into account the presence
    of whitespace before and after it; if not, it will match any presence
    of the word throughout the text, ignoring the whitespace.

    Args:
        word (str): the word to be matched with regex pattern.

    Returns:
        str: the regex pattern for the word.
    """
    rword = re.escape(word)
    if contains_cjko(rword):
        return fr'({rword})'
    else:
        return fr'\b({rword})(?!\w)'


def highlight_content(content, query):

    if not content:
        return None

    # ignoring html contents
    # TODO better html content detection
    if content.find('<') != -1:
        return content

    querysplit = query.split()
    queries = []
    for qs in querysplit:
        qs = qs.replace("'", "").replace('"', '').replace(" ", "")
        if len(qs) > 0:
            queries.extend(re.findall(regex_highlight_cjk(qs), content, flags=re.I | re.U))
    if len(queries) > 0:
        for q in set(queries):
            content = re.sub(
                regex_highlight_cjk(q), f'<span class="highlight">{q}</span>'.replace('\\', r'\\'), content
            )
    return content


def searxng_l10n_timespan(dt: datetime) -> str:  # pylint: disable=invalid-name
    """Returns a human-readable and translated string indicating how long ago
    a date was in the past / the time span of the date to the present.

    On January 1st, midnight, the returned string only indicates how many years
    ago the date was.
    """
    # TODO, check if timezone is calculated right  # pylint: disable=fixme
    d = dt.date()
    t = dt.time()
    if d.month == 1 and d.day == 1 and t.hour == 0 and t.minute == 0 and t.second == 0:
        return str(d.year)
    if dt.replace(tzinfo=None) >= datetime.now() - timedelta(days=1):
        timedifference = datetime.now() - dt.replace(tzinfo=None)
        minutes = int((timedifference.seconds / 60) % 60)
        hours = int(timedifference.seconds / 60 / 60)
        if hours == 0:
            return gettext('{minutes} minute(s) ago').format(minutes=minutes)
        return gettext('{hours} hour(s), {minutes} minute(s) ago').format(hours=hours, minutes=minutes)
    return format_date(dt)


def is_flask_run_cmdline():
    """Check if the application was started using "flask run" command line

    Inspect the callstack.
    See https://github.com/pallets/flask/blob/master/src/flask/__main__.py

    Returns:
        bool: True if the application was started using "flask run".
    """
    frames = inspect.stack()
    if len(frames) < 2:
        return False
    return frames[-2].filename.endswith('flask/cli.py')


NO_SUBGROUPING = 'without further subgrouping'


def group_engines_in_tab(engines: Iterable[Engine]) -> List[Tuple[str, Iterable[Engine]]]:
    """Groups an Iterable of engines by their first non tab category (first subgroup)"""

    def get_subgroup(eng):
        non_tab_categories = [c for c in eng.categories if c not in tabs + [DEFAULT_CATEGORY]]
        return non_tab_categories[0] if len(non_tab_categories) > 0 else NO_SUBGROUPING

    def group_sort_key(group):
        return (group[0] == NO_SUBGROUPING, group[0].lower())

    def engine_sort_key(engine):
        return (engine.about.get('language', ''), engine.name)

    tabs = list(settings['categories_as_tabs'].keys())
    subgroups = itertools.groupby(sorted(engines, key=get_subgroup), get_subgroup)
    sorted_groups = sorted(((name, list(engines)) for name, engines in subgroups), key=group_sort_key)

    ret_val = []
    for groupname, engines in sorted_groups:
        group_bang = '!' + groupname.replace(' ', '_') if groupname != NO_SUBGROUPING else ''
        ret_val.append((groupname, group_bang, sorted(engines, key=engine_sort_key)))

    return ret_val
