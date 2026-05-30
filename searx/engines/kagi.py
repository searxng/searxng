# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine for Kagi API (v1)

Mandatory settings:

- :py:obj:`api_key`
- :py:obj:`kagi_categ`

Supported features:

- Categories (search, news, images, videos)
- Paging
- Safe_search
- Time_range
"""

from json import dumps, loads
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from searx.network import raise_for_httperror
from searx.utils import parse_duration_string

about = {
    "website": "https://www.kagi.com/",
    "wikidata_id": "Q123819301",
    "official_api_documentation": "https://kagi.com/api/docs/openapi/search",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
}

paging = True

time_range_support = True

timeout = 5

api_key = None

kagi_categ = None

api_url = 'https://kagi.com/api/v1/search'

def walk_dict(data, path):
    v = data
    for p in path:
        v = v.get(p)
        if v is None:
            return v
    return v

class MapPath():
    def __init__(self, path):
        self._path = path

    def Map(self, d):
        return walk_dict(d, self._path)

class MapResolutionPath(MapPath):
    def __init__(self, path, width, height):
        super().__init__(path)
        self._width = width
        self._height = height

    def Map(self, d):
        v = super().Map(d)
        if isinstance(v, dict):
            v = f'{v.get(self._width,"")} x {v.get(self._height,"")}'
        return v

class MapTimePath(MapPath):
    def Map(self, d):
        v = super().Map(d)
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class MapDurationPath(MapPath):
    def Map(self, d):
        v = super().Map(d)
        if isinstance(v, str):
            return parse_duration_string(v)
        return v

categ_maps = {
    'search': {
        'result_key': 'search',
        'maps': {
            'url': MapPath(['url']),
            'title': MapPath(['title']),
            'content': MapPath(['snippet']),
            'publishedDate': MapTimePath(['time'])
        }
    },
    'news': {
        'result_key': 'news',
        'maps': {
            'url': MapPath(['url']),
            'title': MapPath(['title']),
            'content': MapPath(['snippet']),
            'publishedDate': MapTimePath(['time'])
        }
    },
    'images': {
        'result_key': 'image',
        'template': 'images.html',
        'maps': {
            'url': MapPath(['image', 'url']),
            'img_src': MapPath(['image', 'url']),
            'resolution': MapResolutionPath(['image'],'width','height'),
            'title': MapPath(['title']),
            'thumbnail': MapPath(['props', 'thumbnail', 'url']),
            'content': MapPath(['url']),
            'publishedDate': MapTimePath(['time'])
        }
    },
    'videos': {
        'result_key': 'video',
        'template': 'videos.html',
        'maps': {
            'url': MapPath(['url']),
            'title': MapPath(['title']),
            'thumbnail': MapPath(['image', 'url']),
            'content': MapPath(['snippet']),
            'publishedDate': MapTimePath(['time']),
            'length': MapDurationPath(['props', 'duration']),
            'views': MapPath(['props', 'view_count']),
            'author': MapPath(['props', 'creator_name'])
        }
    }
}

def get_after(tr):
    tod = date.today()
    if tr == 'day':
        return (tod - relativedelta(days=1)).isoformat()
    elif tr == 'week':
        return (tod - relativedelta(weeks=1)).isoformat()
    elif tr == 'month':
        return (tod - relativedelta(months=1)).isoformat()
    else:
        return (tod - relativedelta(years=1)).isoformat()

def request(query, params):
    if not query:
        return None

    pageno = params.get('pageno',1)

    if pageno > 10:
        return None

    req = {
        'query': query,
        'page': pageno,
        'workflow': kagi_categ
    }

    req['filters'] = { 'safe_search': False if params['safesearch'] == 0 else True }

    if params.get('time_range') is not None:
        req['filters']['after'] = get_after(params['time_range'])

    params['headers']['Authorization'] = f'Bearer {api_key}'
    params['url'] = api_url
    params['method'] = 'POST'
    params['json'] = req

    return params

def response(resp):
    raise_for_httperror(resp)

    results = []

    js = loads(resp.text)

    cmap = categ_maps[kagi_categ]
    rk = cmap['result_key']
    mp = cmap['maps']
    tmpl = cmap.get('template', None)

    for rs in js.get('data', {}).get(rk, []):
        tmp_result = {}
        for k in mp.keys():
            tmp_v = mp[k].Map(rs)
            if tmp_v is not None:
                tmp_result[k] = tmp_v
        if tmpl is not None:
            tmp_result['template'] = tmpl
        results.append(tmp_result)

    return results
