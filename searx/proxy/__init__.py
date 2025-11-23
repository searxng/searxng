# SPDX-License-Identifier: AGPL-3.0-or-later
"""curl_cffi proxy module

This module provides HTTP proxy functionality based on curl_cffi for bypassing anti-crawler detection.
Data model definitions:
- This file - module initialization
"""

from searx.proxy.curl_cffi_proxy import curl_cffi_proxify, is_curl_cffi_proxy_enabled

__all__ = ['curl_cffi_proxify', 'is_curl_cffi_proxy_enabled']

