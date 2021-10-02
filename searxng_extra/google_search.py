from sys import argv, exit

if not len(argv) > 1:
    print('search query required')
    exit(1)

import requests
from json import dumps
from searx.engines import google
from searx.search import default_request_params

request_params = default_request_params()
# Possible params
# request_params['headers']['User-Agent'] = ''
# request_params['category'] = ''
request_params['pageno'] = 1
request_params['language'] = 'en_us'
request_params['time_range'] = ''

params = google.request(argv[1], request_params)

request_args = dict(
    headers=request_params['headers'],
    cookies=request_params['cookies'],
)

if request_params['method'] == 'GET':
    req = requests.get
else:
    req = requests.post
    request_args['data'] = request_params['data']

resp = req(request_params['url'], **request_args)
resp.search_params = request_params
print(dumps(google.response(resp)))
