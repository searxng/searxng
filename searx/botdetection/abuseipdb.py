# SPDX-License-Identifier: AGPL-3.0-or-later
""".. _botdetection.abuseipdb:

Method ``abuseipdb``
-------------------

The ``abuseipdb`` method checks incoming IP addresses against the AbuseIPDB API
to detect malicious IPs. This method requires a valkey DB and an AbuseIPDB API key.

Configuration:

.. code:: toml

   [botdetection.abuseipdb]
   enabled = true
   api_key = "your_api_key_here"
   confidence_threshold = 75
   skip_tor = false
   cache_time = 86400

The method works as follows:

1. First, check if the IP result is cached in valkey
2. If not cached, query the AbuseIPDB API
3. If abuseConfidenceScore >= confidence_threshold:
   - Block the request, UNLESS isTor is true and skip_tor is enabled
4. Cache the result in valkey for the configured cache_time

Environment variables:

- ``SEARXNG_ABUSEIPDB_ENABLED``: Set to "true" to enable the module
- ``SEARXNG_ABUSEIPDB_API_KEY``: Your AbuseIPDB API key
- ``SEARXNG_ABUSEIPDB_CONFIDENCE_THRESHOLD``: Minimum confidence score to block (default: 75)
- ``SEARXNG_ABUSEIPDB_SKIP_TOR``: Set to "true" to skip blocking Tor exit nodes
- ``SEARXNG_ABUSEIPDB_CACHE_TIME``: Cache time in seconds (default: 86400)

Get your free API key at https://www.abuseipdb.com/account/api
"""

import hashlib
import json
import typing as t

import flask
import requests
import valkey
import werkzeug

from searx import logger as searx_logger
from searx.botdetection import config
from searx.botdetection import valkeydb
from searx.botdetection._helpers import too_many_requests

logger = searx_logger.getChild("botdetection.abuseipdb")

ABUSEIPDB_API_URL = "https://api.abuseipdb.com/api/v2"


def _hash_ip(ip_address: str) -> str:
    """Hash IP address for privacy (GDPR compliance)."""
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]


def _cache_key(ip_address: str) -> str:
    return f"abuseipdb:{_hash_ip(ip_address)}"


def _get_valkey_client() -> valkey.Valkey:
    return valkeydb.get_valkey_client()


def _get_cached_result(valkey_client: valkey.Valkey, ip_address: str) -> t.Optional[dict[str, t.Any]]:
    """Get cached abuseipdb result from valkey."""
    cached = valkey_client.get(_cache_key(ip_address))
    if cached:
        try:
            return json.loads(cached)  # type: ignore[arg-type]
        except json.JSONDecodeError:
            logger.warning("Failed to decode cached result for IP: %s", ip_address)
    return None


def _set_cached_result(valkey_client: valkey.Valkey, ip_address: str, result: dict[str, t.Any], cache_time: int):
    """Cache minimal abuseipdb result in valkey (only required fields, IP hashed)."""
    cached_data = {
        "abuseConfidenceScore": result.get("abuseConfidenceScore", 0),
        "isTor": result.get("isTor", False),
    }
    valkey_client.setex(_cache_key(ip_address), cache_time, json.dumps(cached_data))


def check_ip(ip_address: str, cfg: config.Config) -> t.Optional[dict[str, t.Any]]:
    """Check an IP against AbuseIPDB API."""
    api_key = cfg.get("botdetection.abuseipdb.api_key", default="")
    if not api_key:
        logger.warning("AbuseIPDB API key not configured")
        return None

    url = f"{ABUSEIPDB_API_URL}/check"
    params = {
        "ipAddress": ip_address,
        "maxAgeInDays": 90,
    }
    headers = {
        "Accept": "application/json",
        "Key": api_key,
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data")
        if response.status_code == 429:
            logger.warning("AbuseIPDB rate limit exceeded")
            return None
        logger.error("AbuseIPDB API error: %d - %s", response.status_code, response.text)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to query AbuseIPDB for IP %s: %s", ip_address, e)

    return None


def report_ip(ip_address: str, categories: str, comment: str, cfg: config.Config) -> t.Optional[dict[str, t.Any]]:
    """Report an IP to AbuseIPDB."""
    api_key = cfg.get("botdetection.abuseipdb.api_key", default="")
    if not api_key:
        logger.warning("AbuseIPDB API key not configured")
        return None

    url = f"{ABUSEIPDB_API_URL}/report"
    data = {
        "ip": ip_address,
        "categories": categories,
        "comment": comment,
    }
    headers = {
        "Accept": "application/json",
        "Key": api_key,
    }

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("data")
        if response.status_code == 429:
            logger.warning("AbuseIPDB rate limit exceeded")
            return None
        logger.error("AbuseIPDB API error: %d - %s", response.status_code, response.text)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to report to AbuseIPDB for IP %s: %s", ip_address, e)

    return None


def filter_request(
    network: t.Any,
    _request: flask.Request,
    cfg: config.Config,
) -> werkzeug.Response | None:
    """Check IP against AbuseIPDB and block if confidence score is high enough."""
    enabled = cfg.get("botdetection.abuseipdb.enabled", default=False)
    if not enabled:
        return None

    api_key = cfg.get("botdetection.abuseipdb.api_key", default="")
    if not api_key:
        return None

    try:
        valkey_client = _get_valkey_client()
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Failed to get valkey client: %s", e)
        return None

    ip_address = str(network.network_address)
    hashed_ip = _hash_ip(ip_address)
    confidence_threshold = cfg.get("botdetection.abuseipdb.confidence_threshold", default=75)
    skip_tor = cfg.get("botdetection.abuseipdb.skip_tor", default=False)
    cache_time = cfg.get("botdetection.abuseipdb.cache_time", default=86400)

    cached_result: t.Optional[dict[str, t.Any]] = _get_cached_result(valkey_client, hashed_ip)

    if cached_result is None:
        logger.debug("Querying AbuseIPDB for IP: %s", hashed_ip)
        cached_result = check_ip(ip_address, cfg)

        if cached_result is None:
            logger.warning(
                "Failed to get abuseipdb result for IP: %s, allowing request",
                hashed_ip,
            )
            return None

        _set_cached_result(valkey_client, ip_address, cached_result, cache_time)

    abuse_confidence_score: int = cached_result.get("abuseConfidenceScore", 0)
    is_tor: bool = cached_result.get("isTor", False)

    logger.debug(
        "IP %s: abuseConfidenceScore=%d, isTor=%s",
        hashed_ip,
        abuse_confidence_score,
        is_tor,
    )

    if abuse_confidence_score >= confidence_threshold:
        if is_tor and skip_tor:
            logger.debug(
                "IP %s: abuseConfidenceScore=%d >= %d but is Tor exit node and skip_tor is enabled, allowing",
                hashed_ip,
                abuse_confidence_score,
                confidence_threshold,
            )
        else:
            logger.error(
                "BLOCK: IP %s has abuseConfidenceScore %d >= %d",
                hashed_ip,
                abuse_confidence_score,
                confidence_threshold,
            )
            return too_many_requests(network, f"IP has abuse confidence score {abuse_confidence_score}")

    return None
