# SPDX-License-Identifier: AGPL-3.0-or-later
"""Engine for Azure resources. 
This engine mimics the standard search bar in Azure Portal (for resources and resource groups).

To use this engine add the following entry to your engines
list in ``settings.yml``:

.. code:: yaml

  - name: azure
    engine: azure
    shortcut: az
    tenant_id: 'your-tenant-id'
    client_id: 'your-client-id'
    client_secret: 'your-client-secret'
    disabled: false
    categories: [it, cloud]

You must create an App Registration in your Azure Entra Id and assign it the
'Reader' role in your subscription.
"""
import typing as t

from searx.network import post as http_post
from searx.result_types import EngineResults

if t.TYPE_CHECKING:
    from searx.extended_types import SXNG_Response
    from searx.search.processors import OnlineParams

engine_type = "online"
categories = ["it", "cloud"]
# Default values, should be overridden in settings.yml
tenant_id = ""
client_id = ""
client_secret = ""


batch_endpoint = "https://management.azure.com/batch?api-version=2020-06-01"

about = {
    "website": "https://www.portal.azure.com",
    "wikidata_id": "Q725967",
    "official_api_documentation": True,
    "use_official_api": True,
    "require_api_key": True,
    "results": "JSON",
    "language": "en",
}


def authenticate(t_id: str, c_id: str, c_secret: str) -> str:
    """Authenticates to Azure using Oauth2 Client Credentials Flow and returns an access token"""

    url = f"https://login.microsoftonline.com/{t_id}/oauth2/v2.0/token"
    body = {
        "client_id": c_id,
        "client_secret": c_secret,
        "grant_type": "client_credentials",
        "scope": "https://management.azure.com/.default",
    }

    resp: SXNG_Response = http_post(url, body)
    return resp.json()["access_token"]


def request(query: str, params: "OnlineParams") -> None:

    token = authenticate(tenant_id, client_id, client_secret)

    params["url"] = batch_endpoint
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
                    "query": f"ResourceContainers \
                        | where (name contains ('{query}'))\
                        | where (type =~ ('Microsoft.Resources/subscriptions/resourcegroups'))\
                        | project id,name,type,kind,subscriptionId,resourceGroup\
                        | extend matchscore = name startswith '{query}' \
                        | extend normalizedName = tolower(tostring(name)) \
                        | sort by matchscore desc, normalizedName asc \
                        | take 30"
                },
            },
            {
                "url": "/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01",
                "httpMethod": "POST",
                "name": "resources",
                "requestHeaderDetails": {"commandName": "Microsoft.ResourceGraph"},
                "content": {"query": f"Resources | where name contains '{query}' | take 30"},
            },
        ]
    }


def response(resp: "SXNG_Response") -> EngineResults:
    res = EngineResults()
    json_data = resp.json()
    # print(json_data)

    for result in json_data["responses"]:
        if result["name"] == "resourceGroups":
            for data in result["content"]["data"]:
                print(data)
                res.add(
                    res.types.MainResult(
                        url="https://portal.azure.com/#@/resource"
                        + f"/subscriptions/{data['subscriptionId']}/resourceGroups/{data['name']}/overview",
                        title=data["name"],
                        content=f"Resource Group in Subscription: {data['subscriptionId']}",
                    )
                )
        elif result["name"] == "resources":
            for data in result["content"]["data"]:
                print(data)
                res.add(
                    res.types.MainResult(
                        url="https://portal.azure.com/#@/resource"
                        + f"/subscriptions/{data['subscriptionId']}/resourceGroups/{data['resourceGroup']}"
                        + f"/providers/{data['type']}/{data['name']}/overview",
                        title=data["name"],
                        content=f"Resource of type {data['type']} in Subscription:"
                        + f" {data['subscriptionId']}, Resource Group: {data['resourceGroup']}",
                    )
                )
    return res
