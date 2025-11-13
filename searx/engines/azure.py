# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine for Azure resources.  This engine mimics the standard search bar in Azure
Portal (for resources and resource groups).

Configuration
=============

You must `register an application in Microsoft Entra ID`_ and assign it the
'Reader' role in your subscription.

To use this engine, add an entry similar to the following to your engine list in
``settings.yml``:

.. code:: yaml

   - name: azure
     engine: azure
     ...
     azure_tenant_id: "your_tenant_id"
     azure_client_id: "your_client_id"
     azure_client_secret: "your_client_secret"
     azure_token_expiration_seconds: 5000

.. _register an application in Microsoft Entra ID:
    https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app

"""
import typing as t

from searx.enginelib import EngineCache
from searx.network import post as http_post
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

engine_type = "online"
categories = ["it", "cloud"]

# Default values, should be overridden in settings.yml
azure_tenant_id = ""
azure_client_id = ""
azure_client_secret = ""
azure_token_expiration_seconds = 5000
"""Time for which an auth token is valid (sec.)"""
azure_batch_endpoint = "https://management.azure.com/batch?api-version=2020-06-01"

about = {
    "website": "https://www.portal.azure.com",
    "wikidata_id": "Q725967",
    "official_api_documentation": "https://learn.microsoft.com/en-us/\
    rest/api/azure-resourcegraph/?view=rest-azureresourcegraph-resourcegraph-2024-04-01",
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
    "language": "en",
}

CACHE: EngineCache
"""Persistent (SQLite) key/value cache that deletes its values after ``expire``
seconds."""


def setup(engine_settings: dict[str, t.Any]) -> bool:
    """Initialization of the engine.

    - Instantiate a cache for this engine (:py:obj:`CACHE`).
    - Checks whether the tenant_id, client_id and client_secret are set,
      otherwise the engine is inactive.

    """
    global CACHE  # pylint: disable=global-statement
    CACHE = EngineCache(engine_settings["name"])

    missing_opts: list[str] = []
    for opt in ("azure_tenant_id", "azure_client_id", "azure_client_secret"):
        if not engine_settings.get(opt, ""):
            missing_opts.append(opt)
    if missing_opts:
        logger.error("missing values for options: %s", ", ".join(missing_opts))
        return False
    return True


def authenticate(t_id: str, c_id: str, c_secret: str) -> str:
    """Authenticates to Azure using Oauth2 Client Credentials Flow and returns
    an access token."""

    url = f"https://login.microsoftonline.com/{t_id}/oauth2/v2.0/token"
    body = {
        "client_id": c_id,
        "client_secret": c_secret,
        "grant_type": "client_credentials",
        "scope": "https://management.azure.com/.default",
    }

    resp: SXNG_Response = http_post(url, body, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError(f"Azure authentication failed (status {resp.status_code}): {resp.text}")
    return resp.json()["access_token"]


def get_auth_token(t_id: str, c_id: str, c_secret: str) -> str:
    key = f"azure_tenant_id: {t_id:}, azure_client_id: {c_id}, azure_client_secret: {c_secret}"
    token: str | None = CACHE.get(key)
    if token:
        return token
    token = authenticate(t_id, c_id, c_secret)
    CACHE.set(key=key, value=token, expire=azure_token_expiration_seconds)
    return token


def request(query: str, params: "OnlineParams") -> None:

    token = get_auth_token(azure_tenant_id, azure_client_id, azure_client_secret)

    params["url"] = azure_batch_endpoint
    params["method"] = "POST"
    params["headers"]["Authorization"] = f"Bearer {token}"
    params["headers"]["Content-Type"] = "application/json"
    params["json"] = {
        "requests": [
            {
                "url": "/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01",
                "httpMethod": "POST",
                "name": "resourceGroups",
                "requestHeaderDetails": {"commandName": "Microsoft.ResourceGraph"},
                "content": {
                    "query": (
                        f"ResourceContainers"
                        f" | where (name contains ('{query}'))"
                        f" | where (type =~ ('Microsoft.Resources/subscriptions/resourcegroups'))"
                        f" | project id,name,type,kind,subscriptionId,resourceGroup"
                        f" | extend matchscore = name startswith '{query}'"
                        f" | extend normalizedName = tolower(tostring(name))"
                        f" | sort by matchscore desc, normalizedName asc"
                        f" | take 30"
                    )
                },
            },
            {
                "url": "/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01",
                "httpMethod": "POST",
                "name": "resources",
                "requestHeaderDetails": {
                    "commandName": "Microsoft.ResourceGraph",
                },
                "content": {
                    "query": f"Resources | where name contains '{query}' | take 30",
                },
            },
        ]
    }


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_data = resp.json()

    for result in json_data["responses"]:
        if result["name"] == "resourceGroups":
            for data in result["content"]["data"]:
                res.add(
                    res.types.MainResult(
                        url=(
                            f"https://portal.azure.com/#@/resource"
                            f"/subscriptions/{data['subscriptionId']}/resourceGroups/{data['name']}/overview"
                        ),
                        title=data["name"],
                        content=f"Resource Group in Subscription: {data['subscriptionId']}",
                    )
                )
        elif result["name"] == "resources":
            for data in result["content"]["data"]:
                res.add(
                    res.types.MainResult(
                        url=(
                            f"https://portal.azure.com/#@/resource"
                            f"/subscriptions/{data['subscriptionId']}/resourceGroups/{data['resourceGroup']}"
                            f"/providers/{data['type']}/{data['name']}/overview"
                        ),
                        title=data["name"],
                        content=(
                            f"Resource of type {data['type']} in Subscription:"
                            f" {data['subscriptionId']}, Resource Group: {data['resourceGroup']}"
                        ),
                    )
                )
    return res
