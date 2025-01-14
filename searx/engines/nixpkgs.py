# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Nixpkgs Search <https://search.nixos.org>`_ makes it easy to search the huge
nixpkgs package index.  The search backend on search.nixos.org is an
Elasticsearch instance.

Example
=======

The following is an example configuration for an nixpkgs engine with
authentication configured.

Credentials are available here: https://github.com/NixOS/nixos-search/blob/main/frontend/src/index.js

.. code:: yaml

   - name: nixpkgs
     shortcut: nix
     engine: nixpkgs
     base_url: https://search.nixos.org/backend
     username:
     password:
     index: latest-42-nixos-unstable
     channel: unstable

"""

from searx.exceptions import SearxEngineAPIException

about = {
    "website": "https://search.nixos.org",
    "use_official_api": False,
    "require_api_key": True,
    "results": 'JSON',
}
categories = ["it", "packages"]

base_url = "https://search.nixos.org/backend"
username = ""
password = ""
index = "latest-42-nixos-unstable"
channel = "unstable"
search_url = f"{base_url}/{index}/_search"
show_metadata = False
categories = ["it", "packages"]


def init():
    if not (username and password):
        raise ValueError("username and password need to be configured.")


def request(query, params):
    params["auth"] = (username, password)
    params["url"] = search_url
    params["data"] = _build_query(query)
    params["headers"]["Content-Type"] = "application/json"

    return params


def response(resp):
    results = []

    resp_json = resp.json()
    if "error" in resp_json:
        raise SearxEngineAPIException(resp_json["error"])

    for result in resp_json["hits"]["hits"]:
        raw_result = {key: value if not key.startswith("_") else value for key, value in result["_source"].items()}
        r = {
            "template": "packages.html",
            "title": raw_result["package_attr_name"],
            "package_name": raw_result["package_pname"],
            "version": raw_result["package_pversion"],
            "content": raw_result["package_description"] or "",
            "source_code_url": _position_to_github_url(raw_result["package_position"]),
            "url": f"https://search.nixos.org/packages?channel={channel}&show={raw_result['package_attr_name']}",
            "maintainer": ", ".join(raw_result["package_maintainers_set"]),
            "tags": raw_result["package_programs"],
            "license_name": ", ".join(raw_result["package_license_set"]),
            "homepage": next(iter(raw_result["package_homepage"]), None),
        }

        if show_metadata:
            r["metadata"] = {
                "index": result["_index"],
                "id": result["_id"],
                "score": result["_score"],
            }

        results.append(r)

    return results


def _build_query(query: str):
    return f"""
      {{
        "from": 0,
        "size": 50,
        "sort": [
          {{
            "_score": "desc",
            "package_attr_name": "desc",
            "package_pversion": "desc"
          }}
        ],
        "query": {{
          "bool": {{
            "must": [
              {{
                "dis_max": {{
                  "tie_breaker": 0.7,
                  "queries": [
                    {{
                      "multi_match": {{
                        "type": "cross_fields",
                        "query": "{query}",
                        "analyzer": "whitespace",
                        "auto_generate_synonyms_phrase_query": false,
                        "operator": "and",
                        "_name": "multi_match_firefox",
                        "fields": [
                          "package_attr_name^9",
                          "package_attr_name.*^5.3999999999999995",
                          "package_programs^9",
                          "package_programs.*^5.3999999999999995",
                          "package_pname^6",
                          "package_pname.*^3.5999999999999996",
                          "package_description^1.3",
                          "package_description.*^0.78",
                          "package_longDescription^1",
                          "package_longDescription.*^0.6",
                          "flake_name^0.5",
                          "flake_name.*^0.3"
                        ]
                      }}
                    }},
                    {{
                      "wildcard": {{
                        "package_attr_name": {{
                          "value": "*{query}*",
                          "case_insensitive": true
                        }}
                      }}
                    }}
                  ]
                }}
              }}
            ]
          }}
        }}
      }}
    """


def _position_to_github_url(package_position: str):
    path, line = package_position.split(":")
    return f"https://github.com/NixOS/nixpkgs/blob/master/{path}#L{line}"


def _get_codelines(package_name: str):
    code = f"nix-shell -p {package_name}"
    return [(0, code)]
