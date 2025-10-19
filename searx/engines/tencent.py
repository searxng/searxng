# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tencent Cloud Web Search API Engine

Tencent Cloud Web Search API (腾讯云联网搜索API) provides high-quality web search
with excellent Chinese language support.

API Documentation: https://cloud.tencent.com/document/product/1806/121811
"""

import json
import time
import hmac
import hashlib
from datetime import datetime

# Engine metadata
engine_type = 'online'
categories = ['general', 'web']
paging = False
language_support = True
time_range_support = False
safesearch = False

# API配置
base_url = 'https://wsa.tencentcloudapi.com'


def sign(key, msg):
    """生成签名"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_v3(secret_id, secret_key, host, payload, timestamp):  # pylint: disable=too-many-locals
    """
    生成腾讯云API v3签名
    文档: https://cloud.tencent.com/document/api/1806/121815
    """
    # 1. 拼接规范请求串
    http_request_method = 'POST'
    canonical_uri = '/'
    canonical_querystring = ''
    canonical_headers = f'content-type:application/json\nhost:{host}\n'
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
    date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    credential_scope = f'{date}/wsa/tc3_request'
    hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    string_to_sign = f'{algorithm}\n' f'{timestamp}\n' f'{credential_scope}\n' f'{hashed_canonical_request}'

    # 3. 计算签名
    secret_date = sign(f'TC3{secret_key}'.encode('utf-8'), date)
    secret_service = sign(secret_date, 'wsa')
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


def request(query, params):
    """处理搜索请求"""

    # 从 engine_settings 获取配置
    engine_settings = params.get('engine_settings', {})
    api_key = engine_settings.get('api_key', '')
    secret_key_param = engine_settings.get('secret_key', '')
    mode = engine_settings.get('mode', 0)  # 0-自然检索结果(默认)
    cnt = engine_settings.get('cnt', 10)  # 返回结果数量

    if not api_key or not secret_key_param:
        # 如果没有配置 API key，返回空结果
        params['url'] = None
        return params

    # 准备请求参数
    timestamp = int(time.time())
    host = 'wsa.tencentcloudapi.com'

    # 构建请求body
    request_body = {'Query': query, 'Mode': mode}

    # 添加可选参数
    if cnt and cnt > 10:
        request_body['Cnt'] = cnt

    # 如果需要过滤特定域名
    site = engine_settings.get('site', '')
    if site:
        request_body['Site'] = site

    payload = json.dumps(request_body)

    # 生成签名
    authorization = get_signature_v3(api_key, secret_key_param, host, payload, timestamp)

    # 构建请求头
    headers = {
        'Authorization': authorization,
        'Content-Type': 'application/json',
        'Host': host,
        'X-TC-Action': 'SearchPro',
        'X-TC-Version': '2025-05-08',
        'X-TC-Timestamp': str(timestamp),
        'X-TC-Region': '',  # 不需要指定区域
    }

    # 发送请求
    params['url'] = f'https://{host}/'
    params['method'] = 'POST'
    params['headers'] = headers
    params['data'] = payload

    return params


def response(resp):  # pylint: disable=too-many-branches
    """处理API响应"""
    results = []

    try:
        data = json.loads(resp.text)

        # 检查是否有错误
        if 'Response' not in data:
            return results

        response_data = data['Response']

        # 检查错误信息
        if 'Error' in response_data:
            error = response_data['Error']
            error_msg = f"腾讯云API错误: {error.get('Code', 'Unknown')} - {error.get('Message', 'Unknown error')}"
            raise ValueError(error_msg)

        # 解析搜索结果
        pages = response_data.get('Pages', [])

        for page_str in pages:
            try:
                # 每个page是一个JSON字符串
                page = json.loads(page_str)

                result = {
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    'content': page.get('passage', page.get('content', '')),
                }

                # 添加可选字段
                if 'date' in page:
                    result['publishedDate'] = page['date']

                if 'site' in page:
                    result['metadata'] = page['site']

                if 'images' in page and page['images']:
                    result['img_src'] = page['images'][0] if isinstance(page['images'], list) else page['images']

                # 添加缩略图/favicon
                if 'favicon' in page and page['favicon']:
                    result['thumbnail'] = page['favicon']

                # 添加相关性得分（如果有）
                if 'score' in page:
                    result['metadata'] = f"{result.get('metadata', '')} (相关性: {page['score']:.2f})".strip()

                if result['url'] and result['title']:
                    results.append(result)

            except (json.JSONDecodeError, KeyError):
                # 跳过格式错误的结果
                continue

    except json.JSONDecodeError:
        return results
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f'腾讯云搜索API错误: {str(exc)}') from exc

    return results
