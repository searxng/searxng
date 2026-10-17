#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fetch units and property names from :origin:`searx/engines/wikidata.py` engine.

Output files: (:origin:`CI Update data <.github/workflows/data-update.yml>`).
- :origin:`searx/data/wikidata_units.json`
- :origin:`searx/data/wikidata_properties.json`
"""

import json

from searx.engines import wikidata, set_loggers
from searx.data import data_dir
from searx.wikidata_properties import fetch_properties
from searx.wikidata_units import fetch_units

UNITS_DATA_FILE = data_dir / 'wikidata_units.json'
PROPERTIES_DATA_FILE = data_dir / 'wikidata_properties.json'
set_loggers(wikidata, 'wikidata')


if __name__ == '__main__':
    units = fetch_units()
    with UNITS_DATA_FILE.open('w', encoding="utf8") as f:
        json.dump(units, f, indent=4, sort_keys=True, ensure_ascii=False)

    properties = fetch_properties(units)
    with PROPERTIES_DATA_FILE.open('w', encoding="utf8") as f:
        json.dump(properties, f, indent=4, sort_keys=True, ensure_ascii=False)
