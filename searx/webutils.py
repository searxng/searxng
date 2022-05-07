# -*- coding: utf-8 -*-
import os
import pathlib
import csv
import hashlib
import hmac
import re
import inspect
import itertools
from typing import Iterable, List, Tuple, Dict

from io import StringIO
from codecs import getincrementalencoder

from searx import logger, settings
from searx.engines import Engine, OTHER_CATEGORY


VALID_LANGUAGE_CODE = re.compile(r'^[a-z]{2,3}(-[a-zA-Z]{2})?$')

logger = logger.getChild('webutils')


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

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
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data.decode())
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


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


def highlight_content(content, query):

    if not content:
        return None
    # ignoring html contents
    # TODO better html content detection
    if content.find('<') != -1:
        return content

    if content.lower().find(query.lower()) > -1:
        query_regex = '({0})'.format(re.escape(query))
        content = re.sub(query_regex, '<span class="highlight">\\1</span>', content, flags=re.I | re.U)
    else:
        regex_parts = []
        for chunk in query.split():
            chunk = chunk.replace('"', '')
            if len(chunk) == 0:
                continue
            elif len(chunk) == 1:
                regex_parts.append('\\W+{0}\\W+'.format(re.escape(chunk)))
            else:
                regex_parts.append('{0}'.format(re.escape(chunk)))
        query_regex = '({0})'.format('|'.join(regex_parts))
        content = re.sub(query_regex, '<span class="highlight">\\1</span>', content, flags=re.I | re.U)

    return content


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


DEFAULT_GROUP_NAME = 'others'


def group_engines_in_tab(engines: Iterable[Engine]) -> List[Tuple[str, Iterable[Engine]]]:
    """Groups an Iterable of engines by their first non tab category"""

    def get_group(eng):
        non_tab_categories = [
            c for c in eng.categories if c not in list(settings['categories_as_tabs'].keys()) + [OTHER_CATEGORY]
        ]
        return non_tab_categories[0] if len(non_tab_categories) > 0 else DEFAULT_GROUP_NAME

    groups = itertools.groupby(sorted(engines, key=get_group), get_group)

    def group_sort_key(group):
        return (group[0] == DEFAULT_GROUP_NAME, group[0].lower())

    sorted_groups = sorted(((name, list(engines)) for name, engines in groups), key=group_sort_key)

    def engine_sort_key(engine):
        return (engine.about.get('language', ''), engine.name)

    return [(groupname, sorted(engines, key=engine_sort_key)) for groupname, engines in sorted_groups]
