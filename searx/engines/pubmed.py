# SPDX-License-Identifier: AGPL-3.0-or-later
"""
 PubMed (Scholar publications)
"""

from flask_babel import gettext
from lxml import etree
from datetime import datetime
from urllib.parse import urlencode
from searx.network import get

# about
about = {
    "website": 'https://www.ncbi.nlm.nih.gov/pubmed/',
    "wikidata_id": 'Q1540899',
    "official_api_documentation": {
        'url': 'https://www.ncbi.nlm.nih.gov/home/develop/api/',
        'comment': 'More info on api: https://www.ncbi.nlm.nih.gov/books/NBK25501/',
    },
    "use_official_api": True,
    "require_api_key": False,
    "results": 'XML',
}

categories = ['science']

base_url = (
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi' + '?db=pubmed&{query}&retstart={offset}&retmax={hits}'
)

# engine dependent config
number_of_results = 10
pubmed_url = 'https://www.ncbi.nlm.nih.gov/pubmed/'


def request(query, params):
    # basic search
    offset = (params['pageno'] - 1) * number_of_results

    string_args = dict(query=urlencode({'term': query}), offset=offset, hits=number_of_results)

    params['url'] = base_url.format(**string_args)

    return params


def response(resp):
    results = []

    # First retrieve notice of each result
    pubmed_retrieve_api_url = (
        'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?' + 'db=pubmed&retmode=xml&id={pmids_string}'
    )

    pmids_results = etree.XML(resp.content)
    pmids = pmids_results.xpath('//eSearchResult/IdList/Id')
    pmids_string = ''

    for item in pmids:
        pmids_string += item.text + ','

    retrieve_notice_args = dict(pmids_string=pmids_string)

    retrieve_url_encoded = pubmed_retrieve_api_url.format(**retrieve_notice_args)

    search_results_xml = get(retrieve_url_encoded).content
    search_results = etree.XML(search_results_xml).xpath('//PubmedArticleSet/PubmedArticle/MedlineCitation')

    for entry in search_results:
        title = entry.xpath('.//Article/ArticleTitle')[0].text

        pmid = entry.xpath('.//PMID')[0].text
        url = pubmed_url + pmid

        try:
            content = entry.xpath('.//Abstract/AbstractText')[0].text
        except:
            content = gettext('No abstract is available for this publication.')

        #  If a doi is available, add it to the snipppet
        try:
            doi = entry.xpath('.//ELocationID[@EIdType="doi"]')[0].text
            content = 'DOI: {doi} Abstract: {content}'.format(doi=doi, content=content)
        except:
            pass

        if len(content) > 300:
            content = content[0:300] + "..."
        # TODO: center snippet on query term

        res_dict = {'url': url, 'title': title, 'content': content}

        try:
            publishedDate = datetime.strptime(
                entry.xpath('.//DateCreated/Year')[0].text
                + '-'
                + entry.xpath('.//DateCreated/Month')[0].text
                + '-'
                + entry.xpath('.//DateCreated/Day')[0].text,
                '%Y-%m-%d',
            )
            res_dict['publishedDate'] = publishedDate
        except:
            pass

        results.append(res_dict)

        return results
