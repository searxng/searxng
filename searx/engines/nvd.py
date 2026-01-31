# SPDX-License-Identifier: AGPL-3.0-or-later
"""National Vulnerability Database (it)"""

from urllib.parse import urlencode
from datetime import datetime
from searx.result_types import EngineResults

about = {
    "website": 'https://nvd.nist.gov',
    "wikidata_id": "Q6979334",
    "official_api_documentation": None,
    "use_official_api": False,
    "require_api_key": False,
    "results": "JSON",
}

base_url = "https://nvd.nist.gov/extensions/nudp/services/json/nvd/cve/search/results"
categories = ['it']
paging = True
results_per_page = 10


def request(query, params):
    start_index = (params["pageno"] - 1) * results_per_page

    query_params = {
        "resultType": "records",
        "keyword": query,
        "rowCount": results_per_page,
        "offset": start_index,
    }

    params["url"] = f"{base_url}?{urlencode(query_params)}"
    params['headers']['Referer'] = "https://nvd.nist.gov/vuln/search"

    return params


def response(resp) -> EngineResults:
    results = EngineResults()
    search_res = resp.json()

    for item in search_res['response'][0]['grid']['vulnerabilities']:

        cve_id = item["cve"]["id"]
        description = item["cve"]["descriptions"][0]["value"]
        date = datetime.strptime(item["cve"]["published"], "%Y-%m-%dT%H:%M:%S.%f")

        # Extract severity (Low, Medium, High, or Critical) and CVSS score, if available
        info = item["cve"].get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {})
        severity = info.get("baseSeverity")
        cvss_score = info.get("baseScore")

        metadata = ""
        if severity and cvss_score is not None:
            metadata = f"Severity: {severity} | CVSS Score: {cvss_score}"

        results.add(
            results.types.MainResult(
                url=f'https://nvd.nist.gov/vuln/detail/{cve_id}',
                title=cve_id,
                publishedDate=date,
                metadata=metadata,
                content=description,
            )
        )

    return results
