from urllib.parse import urlparse, parse_qsl
import re

from searx import settings
from searx.i18n import gettext

regex = re.compile(r'10\.\d{4,9}/[^\s]+')

name = gettext('Open Access DOI rewrite')
description = gettext('Avoid paywalls by redirecting to open-access versions of publications when available')
default_on = False
preference_section = 'general'

doi_resolvers = settings['doi_resolvers']


def extract_doi(url):
    match = regex.search(url.path)
    if match:
        return match.group(0)
    for _, v in parse_qsl(url.query):
        match = regex.search(v)
        if match:
            return match.group(0)
    return None


def get_doi_resolver(args, preference_doi_resolver):
    doi_resolvers = settings['doi_resolvers']
    doi_resolver = args.get('doi_resolver', preference_doi_resolver)[0]
    if doi_resolver not in doi_resolvers:
        doi_resolver = settings['default_doi_resolver']
    doi_resolver_url = doi_resolvers[doi_resolver]
    return doi_resolver_url


def on_result(request, search, result):
    if 'parsed_url' not in result:
        return True

    doi = extract_doi(result['parsed_url'])
    if doi and len(doi) < 50:
        for suffix in ('/', '.pdf', '.xml', '/full', '/meta', '/abstract'):
            if doi.endswith(suffix):
                doi = doi[:-len(suffix)]
        result['url'] = get_doi_resolver(request.args, request.preferences.get_value('doi_resolver')) + doi
        result['parsed_url'] = urlparse(result['url'])
    return True
