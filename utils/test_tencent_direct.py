#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tencent Cloud Web Search API Direct Test Tool
Tests Tencent API directly to verify credentials and signature algorithm
"""

import json
import time
import hmac
import hashlib
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Error: requests module is required. Install with: pip install requests")
    sys.exit(1)

# Color definitions
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

# Tencent Cloud API configuration
TENCENT_HOST = 'wsa.tencentcloudapi.com'
TENCENT_SERVICE = 'wsa'
TENCENT_ACTION = 'SearchPro'
TENCENT_VERSION = '2025-05-08'

def sign(key, msg):
    """Generate HMAC signature"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_v3(secret_id, secret_key, payload, timestamp):
    """
    Generate Tencent Cloud API v3 signature (TC3-HMAC-SHA256)
    """
    # 1. Build canonical request
    http_request_method = 'POST'
    canonical_uri = '/'
    canonical_querystring = ''
    canonical_headers = f'content-type:application/json\nhost:{TENCENT_HOST}\n'
    signed_headers = 'content-type;host'
    hashed_request_payload = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    
    canonical_request = (
        f'{http_request_method}\n'
        f'{canonical_uri}\n'
        f'{canonical_querystring}\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{hashed_request_payload}'
    )
    
    # 2. 拼接待签名字符串
    algorithm = 'TC3-HMAC-SHA256'
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d')
    credential_scope = f'{date}/{TENCENT_SERVICE}/tc3_request'
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    
    string_to_sign = (
        f'{algorithm}\n'
        f'{timestamp}\n'
        f'{credential_scope}\n'
        f'{hashed_canonical_request}'
    )
    
    # 3. 计算签名
    secret_date = sign(f'TC3{secret_key}'.encode('utf-8'), date)
    secret_service = sign(secret_date, TENCENT_SERVICE)
    secret_signing = sign(secret_service, 'tc3_request')
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 4. 拼接Authorization
    authorization = (
        f'{algorithm} '
        f'Credential={secret_id}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, '
        f'Signature={signature}'
    )
    
    return authorization

def test_tencent_api(query, secret_id, secret_key, mode=0):
    """Test Tencent Cloud API"""
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}Testing query: {query}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"Search mode: {mode} (0=natural/1=multimodal VR/2=mixed)")
    print()

    # Prepare request parameters
    timestamp = int(time.time())
    payload = json.dumps({'Query': query, 'Mode': mode})

    # Generate signature
    print(f"{Colors.YELLOW}Generating TC3-HMAC-SHA256 signature...{Colors.NC}")
    authorization = get_signature_v3(secret_id, secret_key, payload, timestamp)

    # Build request headers
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json',
        'Host': TENCENT_HOST,
        'X-TC-Action': TENCENT_ACTION,
        'X-TC-Version': TENCENT_VERSION,
        'X-TC-Timestamp': str(timestamp),
        'X-TC-Region': '',
    }

    # Send request
    print(f"{Colors.YELLOW}Calling Tencent Cloud API...{Colors.NC}")
    try:
        response = requests.post(f'https://{TENCENT_HOST}/', headers=headers, data=payload, timeout=10)

        print(f"HTTP Status: {Colors.GREEN}✓ {response.status_code} OK{Colors.NC}")

        # Parse response
        data = response.json()

        if 'Response' not in data:
            print(f"{Colors.RED}✗ Invalid response format{Colors.NC}")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return False

        response_data = data['Response']

        # Check for errors
        if 'Error' in response_data:
            error = response_data['Error']
            error_code = error.get('Code', 'Unknown')
            error_message = error.get('Message', 'Unknown error')

            print(f"{Colors.RED}✗ API Error{Colors.NC}")
            print(f"Error Code: {Colors.RED}{error_code}{Colors.NC}")
            print(f"Error Message: {error_message}")

            # Provide suggestions
            suggestions = {
                'AuthFailure.SignatureFailure': 'Signature verification failed, check SecretId and SecretKey',
                'AuthFailure.SecretIdNotFound': 'SecretId not found, verify it is correct',
                'RequestLimitExceeded': 'Rate limit exceeded, retry later or upgrade plan',
                'UnauthorizedOperation': 'Unauthorized operation, check API permissions or enable service\n  Visit: https://console.cloud.tencent.com/wsa',
                'InvalidParameter': 'Invalid parameter, check request parameters',
            }

            if error_code in suggestions:
                print(f"{Colors.YELLOW}Suggestion: {suggestions[error_code]}{Colors.NC}")

            return False

        # Success - got results
        pages = response_data.get('Pages', [])

        if not pages:
            print(f"{Colors.YELLOW}⚠ Warning: API call succeeded but no search results{Colors.NC}")
            return True

        print(f"Results count: {Colors.GREEN}✓ {len(pages)}{Colors.NC}")
        print()

        # Display first 3 results
        for i, page_str in enumerate(pages[:3], 1):
            try:
                page = json.loads(page_str)

                print(f"{Colors.CYAN}Result {i}:{Colors.NC}")
                print(f"  Title: {page.get('title', 'N/A')}")
                print(f"  URL: {page.get('url', 'N/A')}")

                passage = page.get('passage', page.get('content', 'N/A'))
                if len(passage) > 100:
                    passage = passage[:100] + '...'
                print(f"  Summary: {passage}")

                if 'site' in page:
                    print(f"  Source: {page['site']}")
                if 'score' in page:
                    print(f"  Relevance: {page['score']:.4f}")
                if 'date' in page:
                    print(f"  Date: {page['date']}")

                print()
            except json.JSONDecodeError:
                continue

        # Display RequestId
        request_id = response_data.get('RequestId', 'N/A')
        print(f"RequestId: {request_id}")
        print()
        print(f"{Colors.GREEN}✓ Test passed - API call successful{Colors.NC}")

        return True

    except requests.exceptions.Timeout:
        print(f"{Colors.RED}✗ Request timeout{Colors.NC}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}✗ Request failed: {str(e)}{Colors.NC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Unknown error: {str(e)}{Colors.NC}")
        return False

def main():
    """Main function"""
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}Tencent Cloud Web Search API Direct Test Tool{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print()
    print(f"API Endpoint: {Colors.YELLOW}https://{TENCENT_HOST}{Colors.NC}")
    print()

    # Get API credentials
    try:
        secret_id = input("Enter SecretId: ").strip()
        if not secret_id:
            print(f"{Colors.RED}✗ SecretId cannot be empty{Colors.NC}")
            sys.exit(1)

        import getpass

        secret_key = getpass.getpass("Enter SecretKey: ").strip()
        if not secret_key:
            print(f"{Colors.RED}✗ SecretKey cannot be empty{Colors.NC}")
            sys.exit(1)

        print()
        print(f"{Colors.GREEN}✓ Credentials received{Colors.NC}")
        print(f"SecretId: {secret_id[:8]}***{secret_id[-4:]}")
        print()

        # Select search mode
        print("Select search mode:")
        print("  0 - Natural search results (default)")
        print("  1 - Multimodal VR results")
        print("  2 - Mixed results")
        mode_input = input("Enter mode (0/1/2, default 0): ").strip()
        mode = int(mode_input) if mode_input and mode_input in ['0', '1', '2'] else 0
        print()

        # Run tests
        print(f"{Colors.BLUE}Starting tests...{Colors.NC}")
        print()

        test_queries = [("北京天气", "Basic search test"), ("人工智能最新进展", "Tech news search")]

        success_count = 0
        for query, description in test_queries:
            print()
            if test_tencent_api(query, secret_id, secret_key, mode):
                success_count += 1
            print()

        # Ask for more tests
        if success_count > 0:
            continue_test = input(f"{Colors.YELLOW}Continue with more tests? (y/N): {Colors.NC}").strip().lower()
            if continue_test == 'y':
                more_queries = [("腾讯公司", "Company search"), ("OpenAI GPT", "English search test")]
                for query, description in more_queries:
                    print()
                    test_tencent_api(query, secret_id, secret_key, mode)
                    print()

        # Summary
        print()
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
        print(f"{Colors.BLUE}Tests Complete{Colors.NC}")
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
        print()

        if success_count > 0:
            print(f"{Colors.GREEN}✓ Successful tests: {success_count}/{len(test_queries)} queries{Colors.NC}")
            print()
            print(f"{Colors.GREEN}Next step: Configure the engine in SearXNG{Colors.NC}")
            print("Reference: utils/tencent_settings_example.yml")
        else:
            print(f"{Colors.RED}✗ All tests failed{Colors.NC}")
            print()
            print(f"{Colors.YELLOW}Suggestions:{Colors.NC}")
            print("1. Verify SecretId and SecretKey are correct")
            print("2. Ensure Web Search API service is enabled")
            print("   Visit: https://console.cloud.tencent.com/wsa")
            print("3. Check if API quota is exhausted")

    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Test cancelled{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {str(e)}{Colors.NC}")
        sys.exit(1)

if __name__ == '__main__':
    main()

