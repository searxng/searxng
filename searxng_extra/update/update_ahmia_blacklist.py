#!/usr/bin/env python

# This script saves Ahmia's blacklist for onion sites.
# More info in https://ahmia.fi/blacklist/

# set path
from os.path import join

import requests
from searx import searx_dir

URL = 'https://ahmia.fi/blacklist/banned/'


def fetch_ahmia_blacklist():
    resp = requests.get(URL, timeout=3.0)
    if resp.status_code != 200:
        raise Exception("Error fetching Ahmia blacklist, HTTP code " + resp.status_code)
    else:
        blacklist = resp.text.split()
        return blacklist


def get_ahmia_blacklist_filename():
    return join(join(searx_dir, "data"), "ahmia_blacklist.txt")


blacklist = fetch_ahmia_blacklist()
with open(get_ahmia_blacklist_filename(), "w") as f:
    f.write('\n'.join(blacklist))
