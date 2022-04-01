# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Jisho (the Japanese-English dictionary)
"""

import json
from urllib.parse import urlencode, urljoin

# about
about = {
    "website": 'https://jisho.org',
    "wikidata_id": 'Q24568389',
    "official_api_documentation": "https://jisho.org/forum/54fefc1f6e73340b1f160000-is-there-any-kind-of-search-api",
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
    "language": 'ja',
}

categories = ['dictionaries']
engine_type = 'online_dictionary'
paging = False

URL = 'https://jisho.org'
BASE_URL = 'https://jisho.org/word/'
SEARCH_URL = URL + '/api/v1/search/words?{query}'


def request(query, params):
    query = urlencode({'keyword': query})
    params['url'] = SEARCH_URL.format(query=query)
    logger.debug(f"query_url --> {params['url']}")
    return params


def response(resp):
    results = []
    infoboxed = False

    search_results = resp.json()
    pages = search_results.get('data', [])

    for page in pages:
        # Entries that are purely from Wikipedia are excluded.
        if page['senses'][0]['parts_of_speech'] != [] and page['senses'][0]['parts_of_speech'][0] == 'Wikipedia definition':
            pass
        # Process alternative forms
        japanese = page['japanese']
        alt_forms = []
        for title_raw in japanese:
            if 'word' not in title_raw:
                alt_forms.append(title_raw['reading'])
            else:
                title = title_raw['word']
                if 'reading' in title_raw:
                    title += ' (' + title_raw['reading'] + ')'
                alt_forms.append(title)
        # Process definitions
        definitions = []
        def_raw = page['senses']
        for defn_raw in def_raw:
            extra = ''
            if not infoboxed:
                # Extra data. Since they're not documented, this implementation is based solely by the author's assumptions.
                if defn_raw['tags'] != []:
                    if defn_raw['info'] != []:
                        extra += defn_raw['tags'][0] + ', ' + defn_raw['info'][0] + '. ' # "usually written as kana: <kana>"
                    else:
                        extra += ', '.join(defn_raw['tags']) + '. ' # abbreviation, archaism, etc.
                elif defn_raw['info'] != []:
                    extra += ', '.join(defn_raw['info']).capitalize() + '. ' # inconsistent
                if defn_raw['restrictions'] != []:
                    extra += 'Only applies to: ' + ', '.join(defn_raw['restrictions']) + '. '
                extra = extra[:-1]
            definitions.append((
                ', '.join(defn_raw['parts_of_speech']),
                '; '.join(defn_raw['english_definitions']),
                extra
            ))
        content = ''
        infobox_content = '''
            <small><a href="https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project">JMdict</a> 
            and <a href="https://www.edrdg.org/enamdict/enamdict_doc.html">JMnedict</a> 
            by <a href="https://www.edrdg.org/edrdg/licence.html">EDRDG</a>, CC BY-SA 3.0.</small><ul>
            '''
        for pos, engdef, extra in definitions:
            if pos == 'Wikipedia definition':
                infobox_content += '</ul><small>Wikipedia, CC BY-SA 3.0.</small><ul>'
            if pos == '':
                infobox_content += f"<li>{engdef}"
            else:
                infobox_content += f"<li><i>{pos}</i>: {engdef}"
            if extra != '':
                infobox_content += f" ({extra})"
            infobox_content += '</li>'
            content += f"{engdef}. "
        infobox_content += '</ul>'
        
        # For results, we'll return the URL, all alternative forms (as title),
        # and all definitions (as description) truncated to 300 characters.
        results.append({
            'url': urljoin(BASE_URL, page['slug']),
            'title': ", ".join(alt_forms),
            'content': content[:300] + (content[300:] and '...')
        })

        # Like Wordnik, we'll return the first result in an infobox too.
        if not infoboxed:
            infoboxed = True
            infobox_urls = []
            infobox_urls.append({
                'title': 'Jisho.org',
                'url': urljoin(BASE_URL, page['slug'])
            })
            infobox = {
                'infobox': alt_forms[0],
                'urls': infobox_urls
            }
            alt_forms.pop(0)
            alt_content = ''
            if len(alt_forms) > 0:
                alt_content = '<p><i>Other forms:</i> '
                alt_content += ", ".join(alt_forms)
                alt_content += '</p>'
            infobox['content'] = alt_content + infobox_content
            results.append(infobox)

    return results
