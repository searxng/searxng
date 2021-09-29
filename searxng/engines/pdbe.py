# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 PDBe (Protein Data Bank in Europe)
"""

from json import loads
from flask_babel import gettext

# about
about = {
    "website": 'https://www.ebi.ac.uk/pdbe',
    "wikidata_id": 'Q55823905',
    "official_api_documentation": 'https://www.ebi.ac.uk/pdbe/api/doc/search.html',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

categories = ['science']

hide_obsolete = False

# status codes of unpublished entries
pdb_unpublished_codes = ['HPUB', 'HOLD', 'PROC', 'WAIT', 'AUTH', 'AUCO', 'REPL', 'POLC', 'REFI', 'TRSF', 'WDRN']
# url for api query
pdbe_solr_url = 'https://www.ebi.ac.uk/pdbe/search/pdb/select?'
# base url for results
pdbe_entry_url = 'https://www.ebi.ac.uk/pdbe/entry/pdb/{pdb_id}'
# link to preview image of structure
pdbe_preview_url = 'https://www.ebi.ac.uk/pdbe/static/entry/{pdb_id}_deposited_chain_front_image-200x200.png'


def request(query, params):

    params['url'] = pdbe_solr_url
    params['method'] = 'POST'
    params['data'] = {
        'q': query,
        'wt': "json"  # request response in parsable format
    }
    return params


def construct_body(result):
    # set title
    title = result['title']

    # construct content body
    content = """{title} - {authors} {journal} ({volume}) {page} ({year})"""

    # replace placeholders with actual content
    try:
        if result['journal']:
            content = content.format(
                title=result['citation_title'],
                authors=result['entry_author_list'][0], journal=result['journal'], volume=result['journal_volume'],
                page=result['journal_page'], year=result['citation_year'])
        else:
            content = content.format(
                title=result['citation_title'],
                authors=result['entry_author_list'][0], journal='', volume='', page='', year=result['release_year'])
        img_src = pdbe_preview_url.format(pdb_id=result['pdb_id'])
    except (KeyError):
        content = None
        img_src = None

    # construct url for preview image
    try:
        img_src = pdbe_preview_url.format(pdb_id=result['pdb_id'])
    except (KeyError):
        img_src = None

    return [title, content, img_src]


def response(resp):

    results = []
    json = loads(resp.text)['response']['docs']

    # parse results
    for result in json:
        # catch obsolete entries and mark them accordingly
        if result['status'] in pdb_unpublished_codes:
            continue
        if hide_obsolete:
            continue
        if result['status'] == 'OBS':
            # expand title to add some sort of warning message
            title = gettext('{title} (OBSOLETE)').format(title=result['title'])
            try:
                superseded_url = pdbe_entry_url.format(pdb_id=result['superseded_by'])
            except:
                continue

            # since we can't construct a proper body from the response, we'll make up our own
            msg_superseded = gettext("This entry has been superseded by")
            content = '{msg_superseded}: {url} ({pdb_id})'.format(
                msg_superseded=msg_superseded,
                url=superseded_url,
                pdb_id=result['superseded_by'])

            # obsoleted entries don't have preview images
            img_src = None
        else:
            title, content, img_src = construct_body(result)

        results.append({
            'url': pdbe_entry_url.format(pdb_id=result['pdb_id']),
            'title': title,
            'content': content,
            'img_src': img_src
        })

    return results
