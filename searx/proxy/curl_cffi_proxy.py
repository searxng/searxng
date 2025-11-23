# SPDX-License-Identifier: AGPL-3.0-or-later
"""
curl_cffi proxy endpoint implementation

This module provides HTTP proxy functionality based on curl_cffi for bypassing anti-crawler detection.
Data model definitions:
- This file - request/response processing
"""
import base64
import binascii
import json
import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

from flask import request, jsonify, Response
from searx import logger, settings
from searx.webutils import is_hmac_of, new_hmac

logger = logger.getChild('proxy.curl_cffi')

# Default browser fingerprint
DEFAULT_IMPERSONATE = os.environ.get('CURL_CFFI_IMPERSONATE', 'chrome110')


def is_curl_cffi_proxy_enabled() -> bool:
    """Check if curl_cffi proxy is enabled"""
    if not CURL_CFFI_AVAILABLE:
        return False
    
    # Check environment variable first
    env_enabled = os.environ.get('CURL_CFFI_PROXY_ENABLED', '').lower()
    if env_enabled in ('1', 'true', 'yes'):
        return True
    if env_enabled in ('0', 'false', 'no'):
        return False
    
    # Check configuration
    proxy_config = settings.get('outgoing', {}).get('curl_cffi_proxy', {})
    return proxy_config.get('enabled', False)


def curl_cffi_proxy():
    """
    curl_cffi proxy endpoint
    
    Accepts GET requests with parameters:
    - url: Target URL (URL encoded)
    - h: HMAC signature (security verification)
    - method: HTTP method (optional, default GET)
    - impersonate: Browser fingerprint (optional, default chrome110)
    
    Forwards the request as-is and returns the response.
    """
    if not CURL_CFFI_AVAILABLE:
        logger.error("curl_cffi is not installed")
        return '', 503
    
    # Get parameters
    target_url = request.args.get('url')
    if not target_url:
        logger.error("Missing 'url' parameter in curl_cffi_proxy request")
        return '', 400
    
    # URL decoding (Flask's request.args already auto-decodes URLs, but bytes need conversion)
    try:
        if isinstance(target_url, bytes):
            target_url = target_url.decode('utf-8')
        # Ensure it's a string type
        target_url = str(target_url)
    except (UnicodeDecodeError, AttributeError) as e:
        logger.error("Failed to decode URL parameter: %s", e)
        return '', 400
    
    # Verify HMAC signature (security verification)
    hmac_token = request.args.get('h', '')
    if not is_hmac_of(settings['server']['secret_key'], target_url.encode() if isinstance(target_url, str) else target_url, hmac_token):
        logger.warning("Invalid HMAC for curl_cffi_proxy: %s", target_url[:50] if isinstance(target_url, str) else str(target_url)[:50])
        return '', 403
    
    # Get optional parameters
    method = request.args.get('method', 'GET').upper()
    impersonate = request.args.get('impersonate', DEFAULT_IMPERSONATE)
    
    # Get request headers, cookies, etc. from query parameters (base64-encoded JSON)
    # Note: Both GET and POST requests need headers and cookies
    request_headers = {}
    cookies = {}
    
    # Try to get headers from query parameters (base64-encoded JSON)
    headers_b64 = request.args.get('headers')
    if headers_b64:
        try:
            headers_json = base64.b64decode(headers_b64).decode()
            request_headers = json.loads(headers_json)
        except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError, TypeError):
            pass
    
    # Try to get cookies from query parameters (base64-encoded JSON)
    cookies_b64 = request.args.get('cookies')
    if cookies_b64:
        try:
            cookies_json = base64.b64decode(cookies_b64).decode()
            cookies = json.loads(cookies_json)
        except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError, TypeError):
            pass
    
    try:
        # Get proxy configuration (from settings.yml's outgoing.proxies)
        proxy_url = None
        outgoing_proxies = settings.get('outgoing', {}).get('proxies')
        if outgoing_proxies:
            # If proxies is a string, use it directly
            if isinstance(outgoing_proxies, str):
                proxy_url = outgoing_proxies
            # If proxies is a dict, try to get all:// or http:///https://
            elif isinstance(outgoing_proxies, dict):
                proxy_url = outgoing_proxies.get('all://') or outgoing_proxies.get('http://') or outgoing_proxies.get('https://')
                # If it's a list, take the first one
                if isinstance(proxy_url, list):
                    proxy_url = proxy_url[0] if proxy_url else None
        
        # Prepare request parameters (common for GET and POST)
        kwargs: Dict[str, Any] = {
            'headers': request_headers,
            'cookies': cookies,
            'verify': True,
            'allow_redirects': True,
            'timeout': 30.0,
            'impersonate': impersonate,  # curl_cffi feature: browser fingerprint
        }
        
        # If proxy is configured, add it to request parameters
        # curl_cffi uses 'proxy' parameter (string format), not 'proxies'
        # Reference: https://github.com/yifeikong/curl_cffi
        if proxy_url:
            # curl_cffi's proxy parameter accepts string-format proxy URL
            if isinstance(proxy_url, str):
                kwargs['proxy'] = proxy_url
            elif isinstance(proxy_url, dict):
                # If it's a dict, try to extract http or https proxy
                proxy_str = proxy_url.get('http') or proxy_url.get('https') or proxy_url.get('all://')
                if isinstance(proxy_str, list):
                    proxy_str = proxy_str[0] if proxy_str else None
                if proxy_str:
                    kwargs['proxy'] = proxy_str
            logger.debug("Using proxy: %s", kwargs.get('proxy'))
        
        # Handle POST request body (only needed for POST, get from query parameters, base64 encoded)
        if method == 'POST':
            post_data = request.args.get('data')
            if post_data:
                try:
                    # Try to decode base64
                    kwargs['data'] = json.loads(base64.b64decode(post_data).decode())
                except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
                    # If not base64, use directly
                    kwargs['data'] = post_data
            
            post_json = request.args.get('json')
            if post_json:
                try:
                    kwargs['json'] = json.loads(base64.b64decode(post_json).decode())
                except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            post_content = request.args.get('content')
            if post_content:
                try:
                    kwargs['content'] = base64.b64decode(post_content)
                except binascii.Error:
                    pass
        
        # Send request using curl_cffi
        logger.debug("Proxying %s request to %s with impersonate=%s", method, target_url[:100], impersonate)
        response = curl_requests.request(method, target_url, **kwargs)
        
        # Build response headers (only pass necessary ones)
        response_headers = {}
        for key, value in response.headers.items():
            # Filter out some unnecessary response headers
            if key.lower() not in ('content-encoding', 'transfer-encoding', 'connection'):
                response_headers[key] = value
        
        # Return response (as-is)
        return Response(
            response.content,
            status=response.status_code,
            headers=response_headers,
            mimetype=response.headers.get('Content-Type', 'text/html')
        )
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.exception("Error in curl_cffi_proxy for %s: %s (%s)", 
                        target_url[:100] if isinstance(target_url, str) else str(target_url)[:100],
                        error_msg, error_type)
        # Return more detailed error information (for debugging only)
        return jsonify({
            "error": error_msg,
            "error_type": error_type,
            "url": target_url[:200] if isinstance(target_url, str) else str(target_url)[:200]
        }), 500


def curl_cffi_proxify(url: str, method: str = 'GET', impersonate: Optional[str] = None,
                      headers: Optional[Dict[str, str]] = None,
                      cookies: Optional[Dict[str, str]] = None,
                      data: Optional[Any] = None,
                      json_data: Optional[Any] = None,
                      content: Optional[bytes] = None) -> str:
    """
    Convert URL to curl_cffi_proxy URL
    
    Args:
        url: Original URL
        method: HTTP method (GET/POST)
        impersonate: Browser fingerprint (optional)
        headers: Request headers (optional)
        cookies: Cookies (optional)
        data: Form data (optional, for POST)
        json_data: JSON data (optional, for POST)
        content: Binary content (optional, for POST)
    
    Returns:
        Proxy URL, format: http://host:port/curl_cffi_proxy?url=<encoded_URL>&h=<HMAC_signature>&...
    """
    if not url:
        return url
    
    # Check if enabled
    if not is_curl_cffi_proxy_enabled():
        return url
    
    # Skip data URI and relative paths (but allow /curl_cffi_proxy itself)
    if url.startswith('data:') or (url.startswith('/') and not url.startswith('/curl_cffi_proxy')) or url.startswith('#'):
        return url
    
    # Handle protocol-relative URLs
    if url.startswith('//'):
        url = 'https:' + url
    
    # Generate HMAC signature (using original URL's bytes)
    h = new_hmac(settings['server']['secret_key'], url.encode())
    
    # Build parameters (urlencode will handle URL encoding automatically, no need to manually encode)
    params = {
        'url': url,  # Use string, let urlencode handle encoding
        'h': h,
    }
    
    if method != 'GET':
        params['method'] = method
    
    if impersonate and impersonate != DEFAULT_IMPERSONATE:
        params['impersonate'] = impersonate
    
    # Add request headers and cookies (needed for both GET and POST)
    if headers:
        params['headers'] = base64.b64encode(json.dumps(headers).encode()).decode()
    
    if cookies:
        params['cookies'] = base64.b64encode(json.dumps(cookies).encode()).decode()
    
    # Add POST request body
    if method == 'POST':
        if data:
            # Ensure data is bytes or serializable
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode()
            elif isinstance(data, str):
                data_bytes = data.encode()
            else:
                data_bytes = data if isinstance(data, bytes) else str(data).encode()
            params['data'] = base64.b64encode(data_bytes).decode()
        if json_data:
            params['json_data'] = base64.b64encode(json.dumps(json_data).encode()).decode()
        if content:
            params['content'] = base64.b64encode(content).decode()
    
    # Build proxy URL path
    proxy_path = '/curl_cffi_proxy?{0}'.format(urlencode(params))
    
    # Get base_url or build default URL
    base_url = settings.get('server', {}).get('base_url')
    if base_url:
        # If base_url is set, use it
        if base_url.endswith('/'):
            base_url = base_url.rstrip('/')
        return f'{base_url}{proxy_path}'
    else:
        # If base_url is not set, build using bind_address and port
        bind_address = settings.get('server', {}).get('bind_address', '127.0.0.1')
        port = settings.get('server', {}).get('port', 8888)
        return f'http://{bind_address}:{port}{proxy_path}'

