from urllib.parse import urlparse, parse_qsl
from flask_babel import gettext
import re
from searx import settings


regex = re.compile(r'10\.\d{4,9}/[^\s]+')

name = gettext('Open Access DOI rewrite')
description = gettext('Avoid paywalls by redirecting to open-access versions of publications when available')
default_on = False
preference_section = 'general'


def extract_doi(url):
    match = regex.search(url.path)
    if match:
        return match.group(0)
    for _, v in parse_qsl(url.query):
        match = regex.search(v)
        if match:
            return match.group(0)
    return None


def get_doi_resolver(preferences):
    doi_resolvers = settings['doi_resolvers']
    selected_resolver = preferences.get_value('doi_resolver')[0]
    if selected_resolver not in doi_resolvers:
        selected_resolver = settings['default_doi_resolver']
    return doi_resolvers[selected_resolver]


def on_result(request, search, result):
    if 'parsed_url' not in result:
        return True

    doi = extract_doi(result['parsed_url'])
    if doi and len(doi) < 50:
        for suffix in ('/', '.pdf', '.xml', '/full', '/meta', '/abstract'):
            if doi.endswith(suffix):
                doi = doi[: -len(suffix)]
        result['url'] = get_doi_resolver(request.preferences) + doi
        result['parsed_url'] = urlparse(result['url'])
        if 'doi' not in result:
            result['doi'] = doi
    return True
